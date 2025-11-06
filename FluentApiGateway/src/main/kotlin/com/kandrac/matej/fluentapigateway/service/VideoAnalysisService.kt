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
class VideoAnalysisService(
    private val restTemplate: RestTemplate,
) {
    private val logger = LoggerFactory.getLogger(VideoAnalysisService::class.java)

    @Value("\${video.analysis.service.url}")
    private lateinit var videoAnalysisServiceUrl: String

    @Async
    fun triggerVideoAnalysis(videoId: String) {
        try {
            logger.info("Triggering video analysis for video ID: $videoId")

            val url = "$videoAnalysisServiceUrl/api/v1/analyze/video/$videoId/"

            val headers = HttpHeaders()
            headers.contentType = MediaType.APPLICATION_JSON

            val entity = HttpEntity<String>(headers)

            // Make POST request to video analysis microservice
            val response = restTemplate.postForEntity(url, entity, String::class.java)

            if (response.statusCode.is2xxSuccessful) {
                logger.info("Video analysis triggered successfully for video ID: $videoId")
                logger.debug("Response: ${response.body}")
            } else {
                logger.error("Failed to trigger video analysis for video ID: $videoId. Status: ${response.statusCode}")
            }
        } catch (e: Exception) {
            logger.error("Error triggering video analysis for video ID: $videoId", e)
            // Don't throw - this is fire-and-forget
        }
    }
}
