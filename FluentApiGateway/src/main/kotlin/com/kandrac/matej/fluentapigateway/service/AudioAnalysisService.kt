package com.kandrac.matej.fluentapigateway.service

import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.HttpEntity
import org.springframework.http.HttpHeaders
import org.springframework.http.MediaType
import org.springframework.scheduling.annotation.Async
import org.springframework.stereotype.Service
import org.springframework.web.client.RestTemplate

@Service
class AudioAnalysisService(
    private val restTemplate: RestTemplate,
) {
    private val logger = LoggerFactory.getLogger(AudioAnalysisService::class.java)

    @Value("\${audio.analysis.service.url}")
    private lateinit var audioAnalysisServiceUrl: String

    @Async
    fun triggerAudioAnalysis(recordingId: Long) {
        try {
            logger.info("Triggering audio analysis for recording ID: $recordingId")

            val url = "$audioAnalysisServiceUrl/api/v1/audio/$recordingId/analyze/"

            val headers = HttpHeaders()
            headers.contentType = MediaType.APPLICATION_JSON

            val entity = HttpEntity<String>(headers)

            val response = restTemplate.postForEntity(url, entity, String::class.java)

            if (response.statusCode.is2xxSuccessful) {
                logger.info("Audio analysis triggered successfully for recording ID: $recordingId")
                logger.debug("Response: ${response.body}")
            } else {
                logger.error("Failed to trigger audio analysis for recording ID: $recordingId. Status: ${response.statusCode}")
            }
        } catch (e: Exception) {
            logger.error("Error triggering audio analysis for recording ID: $recordingId", e)
        }
    }
}
