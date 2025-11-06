package com.kandrac.matej.fluentapigateway.utils

import org.slf4j.Logger
import org.slf4j.LoggerFactory
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.http.converter.HttpMessageNotReadableException
import org.springframework.web.bind.MissingServletRequestParameterException
import org.springframework.web.bind.annotation.ControllerAdvice
import org.springframework.web.bind.annotation.ExceptionHandler
import org.springframework.web.servlet.NoHandlerFoundException

/**
 * This file defines custom exception handlers for exceptions
 */
@ControllerAdvice
class CustomExceptionHandler {
    private val logger: Logger = LoggerFactory.getLogger(CustomExceptionHandler::class.java)

    @ExceptionHandler(BadRequestException::class)
    fun handle(badRequestException: BadRequestException): ResponseEntity<CustomErrorDetails> =
        ResponseEntity.status(HttpStatus.BAD_REQUEST).body(
            CustomErrorDetails(
                errorDetails = badRequestException.errorDetails,
            ),
        )

    @ExceptionHandler(NotFoundException::class)
    fun handle(notFoundException: NotFoundException): ResponseEntity<CustomErrorDetails> =
        ResponseEntity.status(HttpStatus.NOT_FOUND).body(
            CustomErrorDetails(
                errorDetails = notFoundException.errorDetails,
            ),
        )

    @ExceptionHandler(ForbiddenException::class)
    fun handle(forbiddenException: ForbiddenException): ResponseEntity<CustomErrorDetails> =
        ResponseEntity.status(HttpStatus.FORBIDDEN).body(
            CustomErrorDetails(
                errorDetails = forbiddenException.errorDetails,
            ),
        )

    @ExceptionHandler(UnauthorizedException::class)
    fun handle(unauthorizedException: UnauthorizedException): ResponseEntity<CustomErrorDetails> =
        ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(
            CustomErrorDetails(
                errorDetails = unauthorizedException.errorDetails,
            ),
        )

    @ExceptionHandler(InternalServerErrorException::class)
    fun handle(exception: InternalServerErrorException): ResponseEntity<CustomErrorDetails> =
        ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(
            CustomErrorDetails(
                errorDetails = exception.errorDetails,
            ),
        )

    @ExceptionHandler(NoHandlerFoundException::class)
    fun handle(exception: NoHandlerFoundException): ResponseEntity<CustomErrorDetails> =
        ResponseEntity.status(HttpStatus.NOT_FOUND).body(
            CustomErrorDetails(
                "No handler found ${exception.localizedMessage}",
            ),
        )

    @ExceptionHandler(HttpMessageNotReadableException::class)
    fun handle(exception: HttpMessageNotReadableException): ResponseEntity<CustomErrorDetails> =
        ResponseEntity.status(HttpStatus.BAD_REQUEST).body(
            CustomErrorDetails(
                exception.localizedMessage,
            ),
        )

    @ExceptionHandler(ConflictException::class)
    fun handle(exception: ConflictException): ResponseEntity<CustomErrorDetails> =
        ResponseEntity.status(HttpStatus.CONFLICT).body(
            CustomErrorDetails(
                exception.localizedMessage,
            ),
        )

    @ExceptionHandler(MissingServletRequestParameterException::class)
    fun handle(exception: MissingServletRequestParameterException): ResponseEntity<CustomErrorDetails> =
        ResponseEntity.status(HttpStatus.BAD_REQUEST).body(
            CustomErrorDetails(
                exception.localizedMessage,
            ),
        )

    @ExceptionHandler(Exception::class)
    fun handle(exception: Exception): ResponseEntity<CustomErrorDetails> {
        logger.error("Handling exception without ExceptionHandler $exception", exception)
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(
            CustomErrorDetails(
                "${exception.localizedMessage}, this exception was not handled properly on backend side",
            ),
        )
    }
}

data class CustomErrorDetails(
    val errorDetails: String,
)

/**
 * Following classes contain custom definitions for exceptions.
 * These exceptions are captured in CustomExceptionHandler class and are assigned with specific status codes.
 * This approach makes it easier for services to not require ResponseEntity<RETURN_TYPE> wrapped and use RETURN_TYPE instead.
 * NOTE: There has to be a message in RuntimeException type, because Spring may wrap these errors in ServletException.
 */
data class BadRequestException(
    val errorDetails: String,
) : RuntimeException(errorDetails)

data class NotFoundException(
    val errorDetails: String,
) : RuntimeException(errorDetails)

data class ForbiddenException(
    val errorDetails: String,
) : RuntimeException(errorDetails)

data class UnauthorizedException(
    val errorDetails: String,
) : RuntimeException(errorDetails)

data class InternalServerErrorException(
    val errorDetails: String,
) : RuntimeException(errorDetails)

data class ConflictException(
    val errorDetails: String,
) : RuntimeException(errorDetails)
