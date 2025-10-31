package com.kandrac.matej.fluentapigateway.service

import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service
import org.springframework.web.multipart.MultipartFile
import java.io.IOException
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import java.nio.file.StandardCopyOption
import java.util.*

@Service
class VideoStorageService {

    @Value("\${video.storage.location}")
    private lateinit var storageLocation: String

    private lateinit var rootLocation: Path

    @jakarta.annotation.PostConstruct
    fun init() {
        rootLocation = Paths.get(storageLocation)
        try {
            Files.createDirectories(rootLocation)
        } catch (e: IOException) {
            throw RuntimeException("Could not initialize storage location", e)
        }
    }

    fun storeVideo(file: MultipartFile): String {
        if (file.isEmpty) {
            throw IllegalArgumentException("Failed to store empty file")
        }

        val originalFilename = file.originalFilename ?: "video"
        val fileExtension = originalFilename.substringAfterLast(".", "mp4")
        val uniqueFilename = "${UUID.randomUUID()}.${fileExtension}"

        try {
            val destinationFile = rootLocation.resolve(uniqueFilename).normalize().toAbsolutePath()

            if (!destinationFile.parent.equals(rootLocation.toAbsolutePath())) {
                throw IllegalArgumentException("Cannot store file outside current directory")
            }

            file.inputStream.use { inputStream ->
                Files.copy(inputStream, destinationFile, StandardCopyOption.REPLACE_EXISTING)
            }

            return uniqueFilename
        } catch (e: IOException) {
            throw RuntimeException("Failed to store file", e)
        }
    }

    fun getVideoPath(filename: String): Path {
        return rootLocation.resolve(filename)
    }

    fun deleteVideo(filename: String): Boolean {
        return try {
            val filePath = rootLocation.resolve(filename).normalize()
            Files.deleteIfExists(filePath)
        } catch (e: IOException) {
            false
        }
    }
}
