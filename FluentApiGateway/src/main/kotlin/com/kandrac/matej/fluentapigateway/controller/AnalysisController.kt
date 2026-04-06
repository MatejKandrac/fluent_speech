package com.kandrac.matej.fluentapigateway.controller

import com.kandrac.matej.fluentapigateway.service.AnalysisService
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController

@RestController
@RequestMapping("/api/v1/analysis")
class AnalysisController(
    private val analysisService: AnalysisService,
) {
    @PostMapping("/analyze")
    fun runAnalysis(
        @RequestParam(name = "recording-id", required = true) recordingId: Long,
        @RequestBody(required = false) data: Map<String, Any>?,
    ): ResponseEntity<Any> =
        when (val result = analysisService.forwardAnalysis(recordingId, data)) {
            null -> ResponseEntity.internalServerError().build()
            else -> result
        }
}
