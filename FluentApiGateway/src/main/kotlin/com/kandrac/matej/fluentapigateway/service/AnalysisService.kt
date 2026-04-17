package com.kandrac.matej.fluentapigateway.service

import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import org.apache.hc.client5.http.classic.methods.HttpPost
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient
import org.apache.hc.core5.http.ContentType
import org.apache.hc.core5.http.io.entity.ByteArrayEntity
import org.apache.hc.core5.http.io.entity.EntityUtils
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.stereotype.Service

@Service
class AnalysisService(
    private val httpClient: CloseableHttpClient,
) {
    private val logger = LoggerFactory.getLogger(AnalysisService::class.java)
    private val mapper = jacksonObjectMapper()

    @Value("\${analysis.urls.orchestrator}")
    private lateinit var orchestratorUrl: String

    fun forwardAnalysis(
        recordingId: Long,
        data: Map<String, Any>?,
    ): ResponseEntity<Any>? {
        logger.info("Forwarding analysis for recording $recordingId")
        return try {
            val bodyBytes = mapper.writeValueAsBytes(data ?: emptyMap<String, Any>())
            val request = HttpPost("$orchestratorUrl/api/v1/analyze/$recordingId/")
            request.entity = ByteArrayEntity(bodyBytes, ContentType.APPLICATION_JSON)

            httpClient.execute(request) { response ->
                val raw = EntityUtils.toString(response.entity) ?: "{}"
                val body: Any = runCatching { mapper.readValue(raw, Map::class.java) }.getOrElse { raw }
                ResponseEntity.status(HttpStatus.valueOf(response.code)).body(body)
            }
        } catch (e: Exception) {
            logger.error("Error forwarding analysis for recording $recordingId", e)
            null
        }
    }
}
