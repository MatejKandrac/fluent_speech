package com.kandrac.matej.fluentapigateway.config

import org.slf4j.LoggerFactory
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.security.config.annotation.web.builders.HttpSecurity
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity
import org.springframework.security.config.annotation.web.invoke
import org.springframework.security.config.http.SessionCreationPolicy
import org.springframework.security.web.SecurityFilterChain
import org.springframework.web.cors.CorsConfiguration
import org.springframework.web.cors.CorsConfigurationSource
import org.springframework.web.cors.UrlBasedCorsConfigurationSource

/**
 * SecurityConfiguration class handles setup of key Spring Security capabilities
 */
@Configuration
@EnableWebSecurity
class SecurityConfig {
    private val logger = LoggerFactory.getLogger(SecurityConfig::class.java)

    /**
     * Security filter chain filters all incoming requests via set rules
     */
    @Bean
    fun securityFilterChain(http: HttpSecurity): SecurityFilterChain {
        http {
            csrf {
                disable() // Disable CSRF
            }
            cors {
                disable() // Disable CORS
            }
            authorizeHttpRequests {
                // Allowed requests
                authorize("/api/v1/videos/upload", permitAll)
                // All api endpoints require authentication
                authorize(anyRequest, authenticated)
            }
            sessionManagement {
                sessionCreationPolicy = SessionCreationPolicy.STATELESS
            }
        }

        return http.build()
    }

    /**
     * CORS configuration allows specific requests and methods to pass through.
     * NODE: Do not use corsFilter. It is outdated
     */
    @Bean
    fun corsConfigurationSource(): CorsConfigurationSource? {
        val source = UrlBasedCorsConfigurationSource()
        val config = CorsConfiguration()
        config.allowCredentials = true
        config.allowedOrigins = mutableListOf("*")
        config.allowedHeaders = mutableListOf("*")
        config.allowedMethods = mutableListOf("GET", "POST", "PUT", "OPTIONS", "DELETE", "PATCH")
        source.registerCorsConfiguration("/**", config)
        return source
    }
}
