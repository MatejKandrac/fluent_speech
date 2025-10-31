package com.kandrac.matej.fluentapigateway.dto

data class VideoUploadResponse(
    val success: Boolean,
    val message: String,
    val filename: String? = null,
    val fileSize: Long? = null,
    val uploadedAt: String? = null
)

data class ErrorResponse(
    val success: Boolean = false,
    val message: String
)
