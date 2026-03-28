package com.kandrac.matej.fluentapigateway.service

import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.HttpEntity
import org.springframework.http.HttpHeaders
import org.springframework.http.MediaType
import org.springframework.stereotype.Service
import org.springframework.web.client.RestTemplate

@Service
class AnalysisOrchestratorService(
    private val restTemplate: RestTemplate,
) {
    private val logger = LoggerFactory.getLogger(AnalysisOrchestratorService::class.java)

    @Value("\${analysis.urls.orchestrator}")
    private lateinit var orchestratorUrl: String

    fun runAnalysis(recordingId: Long, flags: Map<String, Boolean>): String? {
        return try {
            val url = "$orchestratorUrl/api/v1/analyze/$recordingId/"
            logger.info("Triggering analysis orchestration for recording ID: $recordingId with flags: $flags")

            val headers = HttpHeaders()
            headers.contentType = MediaType.APPLICATION_JSON

            val entity = HttpEntity(flags, headers)
            val response = restTemplate.postForEntity(url, entity, String::class.java)

            if (response.statusCode.is2xxSuccessful) {
                logger.info("Analysis orchestration completed for recording ID: $recordingId")
            } else {
                logger.error("Orchestration returned non-2xx status ${response.statusCode} for recording ID: $recordingId")
            }

            response.body
        } catch (e: Exception) {
            logger.error("Error calling analysis orchestrator for recording ID: $recordingId", e)
            null
        }
    }
}
