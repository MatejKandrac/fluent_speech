package com.kandrac.matej.fluentapigateway.controller

import com.kandrac.matej.fluentapigateway.service.VideoProcessingService
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController
import org.springframework.web.multipart.MultipartFile

@RestController
@RequestMapping("/api/v1/processing")
class VideoProcessingController(
    private val videoProcessingService: VideoProcessingService,
) {
    @PostMapping("/upload")
    fun uploadVideo(
        @RequestParam("video") video: MultipartFile,
    ): ResponseEntity<Any> =
        when (val result = videoProcessingService.forwardVideo(video)) {
            null -> ResponseEntity.internalServerError().build()
            else -> result
        }

    @GetMapping("/status/{recording-id}")
    fun getProcessingStatus(
        @PathVariable("recording-id") recordingId: Int,
    ): ResponseEntity<Any> =
        when (val result = videoProcessingService.forwardGetStatus(recordingId)) {
            null -> ResponseEntity.internalServerError().build()
            else -> result
        }
}
