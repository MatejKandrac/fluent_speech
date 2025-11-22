package com.kandrac.matej.fluentapigateway.dto

data class VideoUploadResponse(
    val success: Boolean,
    val message: String,
    val videoId: Long? = null,
    val filename: String? = null,
    val fileSize: Long? = null,
    val uploadedAt: String? = null
)
