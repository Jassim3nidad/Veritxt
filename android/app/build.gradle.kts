import java.security.MessageDigest
import java.util.Properties
import groovy.json.JsonSlurper

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
        manifestPlaceholders["appLabel"] = "SmishGuard"
    }
    buildTypes {
        for ((algorithm, label) in listOf("lr" to "Logistic Regression", "nb" to "Naive Bayes", "svm" to "Linear SVM")) {
            create(algorithm) {
                initWith(getByName("debug"))
                applicationIdSuffix = ".$algorithm"
                versionNameSuffix = "-$algorithm-experimental"
                manifestPlaceholders["appLabel"] = "SmishGuard · $label"
                matchingFallbacks += listOf("debug")
            }
        }
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
    sourceSets.getByName("test").resources.srcDir("src/androidTest/assets")
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
for (algorithm in listOf("lr", "nb", "svm")) {
    configurations.getByName("${algorithm}Implementation").extendsFrom(configurations.getByName("debugImplementation"))
    val verify = tasks.register("verify${algorithm.replaceFirstChar { it.uppercase() }}Model") {
        doLast {
            val directory = layout.projectDirectory.dir("src/$algorithm/assets").asFile
            val model = directory.resolve("model.json")
            val review = directory.resolve("review.properties")
            check(model.isFile && review.isFile) { "$algorithm requires a privately reviewed model and review.properties; no model-free fallback." }
            val metadata = Properties().apply { review.inputStream().use { load(it) } }
            check(metadata.getProperty("algorithm") == algorithm && !metadata.getProperty("modelVersion").isNullOrBlank()) { "Wrong algorithm or missing model version" }
            check(metadata.getProperty("manualReview") == "accepted-experimental") { "Local model review is required" }
            val digest = MessageDigest.getInstance("SHA-256").digest(model.readBytes()).joinToString("") { "%02x".format(it) }
            check(digest == metadata.getProperty("sha256")) { "Model changed after review" }
            val content = JsonSlurper().parse(model) as Map<*, *>
            if (content["schema_version"] == 2) {
                check(algorithm == "lr" && digest == "9026c925679f9667b5bd09e34f31dd884cdb72607650d97f9a0708c86fa6bab2") { "Only the reviewed historical LR is supported as schema v2" }
            } else {
                check(content["schema_version"] == 1 && content["algorithm"] == algorithm) { "Export algorithm does not match variant" }
                check(content["synthetic"] == false && content["calibration_evaluated"] == false && content["calibration"] is Map<*, *>) { "Comparison requires an experimental sigmoid export, never a raw-margin percentage or synthetic fixture" }
            }
            check(directory.listFiles()?.map { it.name }?.toSet() == setOf("model.json", "review.properties")) { "Unexpected files in model assets" }
            check(!layout.projectDirectory.file("src/main/assets/model.json").asFile.exists()) { "Shared model asset would contaminate algorithm variants" }
        }
    }
    val title = algorithm.replaceFirstChar { it.uppercase() }
    tasks.matching { it.name == "pre${title}Build" || it.name == "merge${title}Assets" }.configureEach { dependsOn(verify) }
}

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
