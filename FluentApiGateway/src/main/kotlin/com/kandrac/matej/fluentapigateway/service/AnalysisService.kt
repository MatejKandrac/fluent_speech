package com.kandrac.matej.fluentapigateway.service

import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.HttpEntity
import org.springframework.http.HttpHeaders
import org.springframework.http.HttpMethod
import org.springframework.http.MediaType
import org.springframework.http.ResponseEntity
import org.springframework.stereotype.Service
import org.springframework.web.client.RestTemplate
import org.springframework.web.client.exchange
import org.springframework.web.util.UriComponentsBuilder
import java.net.URI

@Service
class AnalysisService(
    private val restTemplate: RestTemplate,
) {
    private val logger = LoggerFactory.getLogger(AnalysisService::class.java)

    @Value("\${analysis.urls.orchestrator}")
    private lateinit var orchestratorUrl: String

    fun forwardAnalysis(
        recordingId: Long,
        data: Map<String, Any>?,
    ): ResponseEntity<Any>? {
        logger.info("Forwarding analysis for recording $recordingId")

        val targetUrl =
            UriComponentsBuilder
                .fromUri(URI.create(orchestratorUrl))
                .queryParam("recording-id", recordingId)
                .toUriString()

        val forwardHeaders =
            HttpHeaders().apply {
                contentType = MediaType.APPLICATION_JSON
            }

        val entity = HttpEntity(data, forwardHeaders)

        return restTemplate.exchange(
            targetUrl,
            HttpMethod.POST,
            entity,
        )
    }
}
