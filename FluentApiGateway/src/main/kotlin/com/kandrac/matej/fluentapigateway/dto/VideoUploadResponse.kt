package com.kandrac.matej.fluentapigateway.dto

data class VideoUploadResponse(
    val success: Boolean,
    val message: String,
    val id: String? = null,
    val filename: String? = null,
    val fileSize: Long? = null,
    val uploadedAt: String? = null
)
