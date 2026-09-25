import java.security.MessageDigest

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}
android {
    namespace = "ph.smishguard"
    compileSdk = 36
    defaultConfig {
        applicationId = "ph.smishguard"
        minSdk = 26
        targetSdk = 36
        versionCode = 2
        versionName = "0.2.0"
        testInstrumentationRunner = "ph.smishguard.SoftwareTestRunner"
    }
    buildTypes {
        create("development") {
            initWith(getByName("debug"))
            applicationIdSuffix = ".dev"
            versionNameSuffix = "-dev"
            matchingFallbacks += listOf("debug")
        }
    }
    testBuildType = providers.gradleProperty("instrumentedBuild").getOrElse("debug")
    buildFeatures { compose = true; buildConfig = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    testOptions { unitTests.isIncludeAndroidResources = true }
    lint { abortOnError = true }
}
kotlin { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) } }
tasks.withType<Test>().configureEach {
    providers.gradleProperty("modelParityDir").orNull?.let {
        systemProperty("smishguard.parity.dir", it)
        inputs.dir(it)
    }
}
configurations.getByName("developmentImplementation").extendsFrom(configurations.getByName("debugImplementation"))

// This private asset is intentionally absent from public checkouts. A development
// APK must never silently fall back to the model-free debug experience.
val verifyDevelopmentModel by tasks.registering {
    val model = layout.projectDirectory.file("src/development/assets/model.json")
    // Always check, including incremental builds after the local asset is removed.
    doLast {
        check(model.asFile.isFile) {
            "Development model missing: place the existing approved 0.2.0-dev asset at " +
                "android/app/src/development/assets/model.json. Do not substitute a candidate model."
        }
        val digest = MessageDigest.getInstance("SHA-256")
            .digest(model.asFile.readBytes()).joinToString("") { "%02x".format(it) }
        check(digest == "9026c925679f9667b5bd09e34f31dd884cdb72607650d97f9a0708c86fa6bab2") {
            "Development model differs from the approved experimental 0.2.0-dev asset."
        }
    }
}
tasks.matching { it.name == "preDevelopmentBuild" || it.name == "mergeDevelopmentAssets" }
    .configureEach { dependsOn(verifyDevelopmentModel) }

dependencies {
    implementation(platform("androidx.compose:compose-bom:2025.12.01"))
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")
    debugImplementation("androidx.compose.ui:ui-tooling")
    implementation("androidx.activity:activity-compose:1.13.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.10.0")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.10.0")
    implementation("androidx.datastore:datastore-preferences:1.2.1")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.11.0")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20260814")
    androidTestImplementation(platform("androidx.compose:compose-bom:2025.12.01"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    androidTestImplementation("androidx.test:runner:1.7.0")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
