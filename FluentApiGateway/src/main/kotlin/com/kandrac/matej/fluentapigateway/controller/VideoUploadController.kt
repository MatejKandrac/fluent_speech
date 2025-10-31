package com.kandrac.matej.fluentapigateway.controller

import com.kandrac.matej.fluentapigateway.dto.ErrorResponse
import com.kandrac.matej.fluentapigateway.dto.VideoUploadResponse
import com.kandrac.matej.fluentapigateway.service.VideoStorageService
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import org.springframework.web.multipart.MultipartFile
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

@RestController
@RequestMapping("/api/videos")
class VideoUploadController(
    private val videoStorageService: VideoStorageService
) {

    @PostMapping("/upload")
    fun uploadVideo(@RequestParam("video") file: MultipartFile): ResponseEntity<Any> {
        return try {
            // Validate file
            if (file.isEmpty) {
                return ResponseEntity
                    .badRequest()
                    .body(ErrorResponse(message = "Please select a video file to upload"))
            }

            // Validate file type (optional - add more video formats as needed)
            val contentType = file.contentType
            if (contentType == null || !isVideoFile(contentType)) {
                return ResponseEntity
                    .badRequest()
                    .body(ErrorResponse(message = "File must be a video (mp4, mov, avi, etc.)"))
            }

            // Store the video
            val savedFilename = videoStorageService.storeVideo(file)

            // Create response
            val response = VideoUploadResponse(
                success = true,
                message = "Video uploaded successfully",
                filename = savedFilename,
                fileSize = file.size,
                uploadedAt = LocalDateTime.now().format(DateTimeFormatter.ISO_DATE_TIME)
            )

            ResponseEntity.ok(response)
        } catch (e: IllegalArgumentException) {
            ResponseEntity
                .badRequest()
                .body(ErrorResponse(message = e.message ?: "Invalid request"))
        } catch (e: Exception) {
            ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ErrorResponse(message = "Failed to upload video: ${e.message}"))
        }
    }

    @DeleteMapping("/{filename}")
    fun deleteVideo(@PathVariable filename: String): ResponseEntity<Any> {
        return try {
            val deleted = videoStorageService.deleteVideo(filename)
            if (deleted) {
                ResponseEntity.ok(VideoUploadResponse(
                    success = true,
                    message = "Video deleted successfully",
                    filename = filename
                ))
            } else {
                ResponseEntity
                    .status(HttpStatus.NOT_FOUND)
                    .body(ErrorResponse(message = "Video not found"))
            }
        } catch (e: Exception) {
            ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ErrorResponse(message = "Failed to delete video: ${e.message}"))
        }
    }

    private fun isVideoFile(contentType: String): Boolean {
        val videoTypes = listOf(
            "video/mp4",
            "video/mpeg",
            "video/quicktime",
            "video/x-msvideo",
            "video/x-ms-wmv",
            "video/webm",
            "video/3gpp",
            "video/3gpp2"
        )
        return videoTypes.any { contentType.startsWith(it) }
    }
}
