package com.kandrac.matej.fluentapigateway.service

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import org.apache.hc.client5.http.classic.methods.HttpGet
import org.apache.hc.client5.http.classic.methods.HttpPost
import org.apache.hc.client5.http.entity.mime.MultipartEntityBuilder
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient
import org.apache.hc.core5.http.ContentType
import org.apache.hc.core5.http.io.entity.EntityUtils
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.stereotype.Service
import org.springframework.web.multipart.MultipartFile

@Service
class VideoProcessingService(
    private val httpClient: CloseableHttpClient,
) {
    private val logger = LoggerFactory.getLogger(VideoProcessingService::class.java)
    private val mapper = jacksonObjectMapper()

    @Value("\${processing.urls.orchestrator}")
    private lateinit var orchestratorUrl: String

    fun forwardVideo(video: MultipartFile): ResponseEntity<Any>? {
        logger.info("Forwarding video upload to processing orchestrator")
        return try {
            val contentType = ContentType.create(
                video.contentType?.takeIf { it.isNotBlank() } ?: "video/mp4"
            )
            val entity = MultipartEntityBuilder.create()
                .addBinaryBody("file", video.bytes, contentType, video.originalFilename ?: "upload")
                .build()

            val request = HttpPost("$orchestratorUrl/api/v1/processing/upload/")
            request.entity = entity

            httpClient.execute(request) { response ->
                val raw = EntityUtils.toString(response.entity) ?: "{}"
                val body: Any = runCatching { mapper.readValue<Map<String, Any>>(raw) }.getOrElse { raw }
                ResponseEntity.status(HttpStatus.valueOf(response.code)).body(body)
            }
        } catch (e: Exception) {
            logger.error("Error forwarding video upload", e)
            null
        }
    }

    fun forwardGetStatus(recordingId: Int): ResponseEntity<Any>? {
        logger.info("Forwarding status request for recording $recordingId")
        return try {
            val request = HttpGet("$orchestratorUrl/api/v1/processing/status?recording-id=$recordingId")
            httpClient.execute(request) { response ->
                val raw = EntityUtils.toString(response.entity) ?: "{}"
                val body: Any = runCatching { mapper.readValue<Map<String, Any>>(raw) }.getOrElse { raw }
                ResponseEntity.status(HttpStatus.valueOf(response.code)).body(body)
            }
        } catch (e: Exception) {
            logger.error("Error forwarding status request for recording $recordingId", e)
            null
        }
    }
}