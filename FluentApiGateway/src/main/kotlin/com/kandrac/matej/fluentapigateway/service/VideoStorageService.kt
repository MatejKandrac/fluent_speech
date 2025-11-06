package com.kandrac.matej.fluentapigateway.service

import com.kandrac.matej.fluentapigateway.dto.VideoUploadResponse
import com.kandrac.matej.fluentapigateway.model.StoredVideo
import com.kandrac.matej.fluentapigateway.repository.VideoRepository
import com.kandrac.matej.fluentapigateway.utils.BadRequestException
import com.kandrac.matej.fluentapigateway.utils.InternalServerErrorException
import com.kandrac.matej.fluentapigateway.utils.NotFoundException
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service
import org.springframework.web.multipart.MultipartFile
import java.io.IOException
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import java.nio.file.StandardCopyOption
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.util.UUID

@Service
class VideoStorageService {
    @Value("\${video.storage.location}")
    private lateinit var storageLocation: String

    private lateinit var rootLocation: Path

    @Autowired
    private lateinit var repository: VideoRepository

    @jakarta.annotation.PostConstruct
    fun init() {
        rootLocation = Paths.get(storageLocation)
        try {
            Files.createDirectories(rootLocation)
        } catch (e: IOException) {
            throw RuntimeException("Could not initialize storage location", e)
        }
    }

    fun handleUploadRequest(file: MultipartFile): VideoUploadResponse {
        if (file.isEmpty) throw BadRequestException("Please select a video file to upload")

        val contentType = file.contentType
        if (contentType == null || !isVideoFile(contentType)) {
            throw BadRequestException("File must be a video (mp4, mov, avi, etc.)")
        }

        // Store the video and get the saved video record
        val savedVideo = storeVideo(file)

        // Create response
        val response =
            VideoUploadResponse(
                success = true,
                message = "Video uploaded successfully",
                id = savedVideo.id,
                filename = savedVideo.filename,
                fileSize = file.size,
                uploadedAt = LocalDateTime.now().format(DateTimeFormatter.ISO_DATE_TIME),
            )

        return response
    }

    fun handleDeleteRequest(filename: String) {
        val deleted = deleteVideo(filename)
        if (!deleted) {
            NotFoundException("File not found")
        }
    }

    private fun storeVideo(file: MultipartFile): StoredVideo {
        val originalFilename = file.originalFilename ?: "video"
        val fileExtension = originalFilename.substringAfterLast(".", "mp4")
        val uniqueFilename = "${UUID.randomUUID()}.$fileExtension"

        try {
            val destinationFile = rootLocation.resolve(uniqueFilename).normalize().toAbsolutePath()

            if (!destinationFile.parent.equals(rootLocation.toAbsolutePath())) {
                throw InternalServerErrorException("Cannot store file outside current directory")
            }

            file.inputStream.use { inputStream ->
                Files.copy(inputStream, destinationFile, StandardCopyOption.REPLACE_EXISTING)
            }

            val video =
                StoredVideo(
                    filename = uniqueFilename,
                )

            val savedVideo = repository.save(video)

            return savedVideo
        } catch (e: IOException) {
            throw InternalServerErrorException("Failed to store file. ${e.message}")
        }
    }

    private fun deleteVideo(filename: String): Boolean =
        try {
            val filePath = rootLocation.resolve(filename).normalize()
            Files.deleteIfExists(filePath)
        } catch (e: IOException) {
            false
        }

    private fun isVideoFile(contentType: String): Boolean {
        val videoTypes =
            listOf(
                "video/mp4",
                "video/mpeg",
                "video/quicktime",
                "video/x-msvideo",
                "video/x-ms-wmv",
                "video/webm",
                "video/3gpp",
                "video/3gpp2",
            )
        return videoTypes.any { contentType.startsWith(it) }
    }
}
