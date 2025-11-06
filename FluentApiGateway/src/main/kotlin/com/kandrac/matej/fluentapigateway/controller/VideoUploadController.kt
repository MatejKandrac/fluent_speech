package com.kandrac.matej.fluentapigateway.controller

import com.kandrac.matej.fluentapigateway.dto.VideoUploadResponse
import com.kandrac.matej.fluentapigateway.service.VideoStorageService
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import org.springframework.web.multipart.MultipartFile

@RestController
@RequestMapping("/api/v1/videos")
class VideoUploadController(
    private val videoStorageService: VideoStorageService,
) {
    @PostMapping("/upload")
    fun uploadVideo(
        @RequestParam("video") file: MultipartFile,
    ): VideoUploadResponse = videoStorageService.handleUploadRequest(file)

    @DeleteMapping("/{filename}")
    fun deleteVideo(
        @PathVariable filename: String,
    ): ResponseEntity<Void> {
        videoStorageService.handleDeleteRequest(filename)
        return ResponseEntity.noContent().build()
    }
}
