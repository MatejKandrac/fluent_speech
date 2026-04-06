package com.kandrac.matej.fluentapigateway.service

import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.core.io.ByteArrayResource
import org.springframework.http.HttpEntity
import org.springframework.http.HttpHeaders
import org.springframework.http.HttpMethod
import org.springframework.http.MediaType
import org.springframework.http.ResponseEntity
import org.springframework.stereotype.Service
import org.springframework.util.LinkedMultiValueMap
import org.springframework.web.client.RestTemplate
import org.springframework.web.multipart.MultipartFile

@Service
class VideoProcessingService(
    private val restTemplate: RestTemplate,
) {
    private val logger = LoggerFactory.getLogger(VideoProcessingService::class.java)

    @Value("\${processing.urls.orchestrator}")
    private lateinit var orchestratorUrl: String

    fun forwardVideo(video: MultipartFile): ResponseEntity<Any>? {
        logger.info("Forwarding video upload to processing orchestrator")
        return try {
            val resource = object : ByteArrayResource(video.bytes) {
                override fun getFilename() = video.originalFilename ?: "upload"
            }
            val body = LinkedMultiValueMap<String, Any>().apply {
                add("file", resource)
            }
            val headers = HttpHeaders().apply {
                contentType = MediaType.MULTIPART_FORM_DATA
            }
            restTemplate.exchange(
                "$orchestratorUrl/api/v1/upload/",
                HttpMethod.POST,
                HttpEntity(body, headers),
                Any::class.java,
            )
        } catch (e: Exception) {
            logger.error("Error forwarding video upload", e)
            null
        }
    }

    fun forwardGetStatus(recordingId: Int): ResponseEntity<Any>? {
        logger.info("Forwarding status request for recording $recordingId")
        return try {
            restTemplate.exchange(
                "$orchestratorUrl/api/v1/status/?recording-id=$recordingId",
                HttpMethod.GET,
                HttpEntity.EMPTY,
                Any::class.java,
            )
        } catch (e: Exception) {
            logger.error("Error forwarding status request for recording $recordingId", e)
            null
        }
    }
}
