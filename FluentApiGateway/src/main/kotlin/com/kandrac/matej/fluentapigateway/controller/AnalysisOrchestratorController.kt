package com.kandrac.matej.fluentapigateway.controller

import com.kandrac.matej.fluentapigateway.service.AnalysisOrchestratorService
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/api/v1/analysis")
class AnalysisOrchestratorController(
    private val orchestratorService: AnalysisOrchestratorService,
) {
    /**
     * Run analysis for a recording.
     *
     * Request body (all flags optional, default: all true when body is empty):
     * {
     *   "arm_movement":  true,
     *   "eye_contact":   true,
     *   "pitch":         true,
     *   "volume":        true,
     *   "hip":           true,
     *   "filler_words":  true
     * }
     */
    @PostMapping("/{recordingId}/run")
    fun runAnalysis(
        @PathVariable recordingId: Long,
        @RequestBody(required = false) flags: Map<String, Boolean>?,
    ): ResponseEntity<String> {
        val resolvedFlags = flags ?: emptyMap()
        val result = orchestratorService.runAnalysis(recordingId, resolvedFlags)
            ?: return ResponseEntity.internalServerError().body("{\"success\":false,\"error\":\"Orchestrator unavailable\"}")
        return ResponseEntity.ok(result)
    }
}
