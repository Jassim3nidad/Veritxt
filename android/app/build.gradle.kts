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
        versionCode = 3
        versionName = "0.3.0"
        testInstrumentationRunner = "ph.smishguard.SoftwareTestRunner"
        manifestPlaceholders["appLabel"] = "Veritxt"
    }
    buildTypes {
        create("mbertQuantized") {
            initWith(getByName("debug"))
            applicationIdSuffix = ".mbert.int8"
            versionNameSuffix = "-mbert-int8-experimental"
            manifestPlaceholders["appLabel"] = "Veritxt · mBERT INT8"
            matchingFallbacks += listOf("debug")
        }
        create("mbert") {
            initWith(getByName("debug"))
            applicationIdSuffix = ".mbert"
            versionNameSuffix = "-mbert-exploratory"
            manifestPlaceholders["appLabel"] = "Veritxt · mBERT"
            matchingFallbacks += listOf("debug")
        }
        create("lrCalibrated4") {
            initWith(getByName("debug"))
            applicationIdSuffix = ".lr.calibrated4"
            versionNameSuffix = "-lr-calibrated-4-experimental"
            manifestPlaceholders["appLabel"] = "Veritxt · LR Calibrated 4"
            matchingFallbacks += listOf("debug")
        }
        create("lrCandidate") {
            initWith(getByName("debug"))
            applicationIdSuffix = ".lr.candidate"
            versionNameSuffix = "-lr-candidate-experimental"
            manifestPlaceholders["appLabel"] = "Veritxt · LR Candidate"
            matchingFallbacks += listOf("debug")
        }
        for ((algorithm, label) in listOf("lr" to "LR", "nb" to "NB", "svm" to "SVM")) {
            create(algorithm) {
                initWith(getByName("debug"))
                applicationIdSuffix = ".$algorithm"
                versionNameSuffix = "-$algorithm-experimental"
                manifestPlaceholders["appLabel"] = "Veritxt · $label"
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
    if (testBuildType in listOf("mbert", "mbertQuantized")) sourceSets.getByName("androidTest").java.srcDir("src/mbertAndroidTest/java")
    sourceSets.getByName("mbertQuantized").java.srcDir("src/mbert/java")
    buildFeatures { compose = true; buildConfig = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    testOptions { unitTests.isIncludeAndroidResources = true }
    sourceSets.getByName("test").resources.srcDir("src/androidTest/assets")
    sourceSets.getByName("test").java.srcDir("src/softwareTest/java")
    sourceSets.getByName("androidTest").java.srcDir("src/softwareTest/java")
    lint { abortOnError = true }
    androidResources { noCompress += "onnx" }
}
kotlin { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) } }
tasks.withType<Test>().configureEach {
    providers.gradleProperty("mbertParityDir").orNull?.let {
        systemProperty("smishguard.mbert.parity.dir", it)
        inputs.dir(it)
    }
    providers.gradleProperty("foldedParityDir").orNull?.let {
        systemProperty("smishguard.folded.parity.dir", it)
        inputs.dir(it)
    }
    providers.gradleProperty("candidateParityDir").orNull?.let {
        systemProperty("smishguard.candidate.parity.dir", it)
        inputs.dir(it)
    }
    providers.gradleProperty("modelParityDir").orNull?.let {
        systemProperty("smishguard.parity.dir", it)
        inputs.dir(it)
    }
}
configurations.getByName("developmentImplementation").extendsFrom(configurations.getByName("debugImplementation"))
configurations.getByName("mbertImplementation").extendsFrom(configurations.getByName("debugImplementation"))
configurations.getByName("mbertQuantizedImplementation").extendsFrom(configurations.getByName("debugImplementation"))
val verifyMbertQuantizedModel by tasks.registering {
    doLast {
        val directory = layout.projectDirectory.dir("src/mbertQuantized/assets").asFile
        val original = layout.projectDirectory.dir("src/mbert/assets").asFile
        fun sha(file: java.io.File): String {
            val digest = MessageDigest.getInstance("SHA-256")
            file.inputStream().use { input ->
                val block = ByteArray(1024 * 1024)
                while (true) { val n = input.read(block); if (n < 0) break; digest.update(block, 0, n) }
            }
            return digest.digest().joinToString("") { "%02x".format(it) }
        }
        check(directory.listFiles()?.map { it.name }?.toSet() == setOf("model.json", "model.onnx", "vocab.txt", "LICENSE.txt")) { "Unexpected experimental assets" }
        val variant = JsonSlurper().parse(directory.resolve("model.json")) as Map<*, *>
        val reference = JsonSlurper().parse(original.resolve("model.json")) as Map<*, *>
        check(variant["quantized"] == true && variant["precision"] == "int8_dynamic" &&
            variant["evaluation_status"] == "experimental_quantization" &&
            variant["reference_model_sha256"] == sha(original.resolve("model.onnx")) &&
            variant["model_sha256"] == sha(directory.resolve("model.onnx")) &&
            variant["vocab_sha256"] == sha(directory.resolve("vocab.txt"))) { "INT8 experiment identity mismatch" }
        for (key in listOf("schema_version", "algorithm", "base_model", "revision", "max_length", "classes", "positive_class",
            "threshold", "threshold_comparison", "calibration", "tokenizer", "vocab_sha256", "score_transform",
            "assessability_vocabulary", "automatic_warnings_approved", "synthetic", "protocol_sha256")) {
            check(variant[key] == reference[key]) { "INT8 experiment changed frozen inference policy: $key" }
        }
        check(variant["automatic_warnings_approved"] == false && reference["quantized"] == false)
        check(!layout.projectDirectory.file("src/main/assets/model.json").asFile.exists()) { "Shared model contamination" }
    }
}
tasks.matching { it.name == "preMbertQuantizedBuild" || it.name == "mergeMbertQuantizedAssets" }.configureEach { dependsOn(verifyMbertQuantizedModel) }
providers.gradleProperty("mbertParityDir").orNull?.let {
    android.sourceSets.getByName("androidTest").assets.srcDir("$it/android-test-assets")
}
val verifyMbertModel by tasks.registering {
    doLast {
        val directory = layout.projectDirectory.dir("src/mbert/assets").asFile
        val metadata = directory.resolve("model.json")
        check(metadata.isFile) { "mBERT requires its actual private frozen export; no placeholder fallback" }
        val content = JsonSlurper().parse(metadata) as Map<*, *>
        fun sha(name: String): String {
            val digest = MessageDigest.getInstance("SHA-256")
            directory.resolve(name).inputStream().use { input ->
                val block = ByteArray(1024 * 1024)
                while (true) { val n = input.read(block); if (n < 0) break; digest.update(block, 0, n) }
            }
            return digest.digest().joinToString("") { "%02x".format(it) }
        }
        check(content["schema_version"] == 5 && content["algorithm"] == "mbert" &&
            content["base_model"] == "google-bert/bert-base-multilingual-cased" &&
            content["revision"] == "3f076fdb1ab68d5b2880cb87a0886f315b8146f8" &&
            content["model_sha256"] == sha("model.onnx") && content["vocab_sha256"] == sha("vocab.txt") &&
            content["synthetic"] == false && content["automatic_warnings_approved"] == false &&
            content["evaluation_status"] == "preliminary_retrospective" && content["quantized"] == false) { "mBERT identity/policy mismatch" }
        check(directory.listFiles()?.map { it.name }?.toSet() == setOf("model.json", "model.onnx", "vocab.txt", "LICENSE.txt")) { "Unexpected mBERT assets" }
        if ((content["model_version"] as? String)?.startsWith("expanded-20261005-") == true) {
            val protocol = rootProject.file("docs/expanded-comparison-protocol-20261005.md")
            val protocolHash = MessageDigest.getInstance("SHA-256").digest(protocol.readBytes()).joinToString("") { "%02x".format(it) }
            check(content["protocol_sha256"] == protocolHash && content["classes"] == listOf("ham", "smishing") &&
                content["positive_class"] == "smishing" && content["threshold_comparison"] == "greater_or_equal" &&
                content["score_transform"] == "sigmoid_of_logit_difference" &&
                (content["calibration"] as? Map<*, *>)?.get("fit_partition") == "calibration") { "Expanded mBERT protocol/class/calibration mismatch" }
        }
        check(!layout.projectDirectory.file("src/main/assets/model.json").asFile.exists()) { "Shared model contamination" }
    }
}
tasks.matching { it.name == "preMbertBuild" || it.name == "mergeMbertAssets" }.configureEach { dependsOn(verifyMbertModel) }
configurations.getByName("lrCandidateImplementation").extendsFrom(configurations.getByName("debugImplementation"))
configurations.getByName("lrCalibrated4Implementation").extendsFrom(configurations.getByName("debugImplementation"))
providers.gradleProperty("foldedParityDir").orNull?.let {
    android.sourceSets.getByName("androidTest").assets.srcDir("$it/android-test-assets")
}
providers.gradleProperty("modelParityDir").orNull?.let {
    android.sourceSets.getByName("androidTest").assets.srcDir("$it/android-test-assets")
}
val verifyLrCalibrated4Model by tasks.registering {
    doLast {
        val directory = layout.projectDirectory.dir("src/lrCalibrated4/assets").asFile
        val model = directory.resolve("model.json")
        val review = directory.resolve("review.properties")
        check(model.isFile && review.isFile) { "Folded LR candidate requires private audited assets" }
        val metadata = Properties().apply { review.inputStream().use { load(it) } }
        val digest = MessageDigest.getInstance("SHA-256").digest(model.readBytes()).joinToString("") { "%02x".format(it) }
        check(metadata.getProperty("sha256") == digest && metadata.getProperty("modelVersion") == "lr-calibrated-4" &&
            metadata.getProperty("algorithm") == "lr") { "Folded candidate identity mismatch" }
        check(metadata.getProperty("reviewKind") == "automated-pattern-screen" && metadata.getProperty("humanReview") == "not_recorded" &&
            metadata.getProperty("reviewReference") == "lr-calibrated-4-audit-20261001") { "State actual automated review; do not fabricate human approval" }
        val content = JsonSlurper().parse(model) as Map<*, *>
        val provenance = content["provenance"] as? Map<*, *>
        val sourceHash = "d91f010a004e1fcfef6e4567389007cb81d16e1f6d0f258c263483b2b60d0d77"
        check(provenance?.get("source_sha256") == sourceHash && metadata.getProperty("sourceSha256") == sourceHash) { "Wrong folded candidate source" }
        check(content["schema_version"] == 4 && content["algorithm"] == "lr" && content["model_version"] == "lr-calibrated-4" &&
            content["calibration_encoding"] == "folded_into_parameters" && !content.containsKey("calibration") &&
            !content.containsKey("calibration_a") && !content.containsKey("calibration_b") &&
            content["calibration_status"] == "fitted_unvalidated" && content["evaluation_status"] == "unverified" &&
            (content["threshold"] as? Number)?.toDouble() == 0.5 && content["threshold_comparison"] == "strict_greater" &&
            content["synthetic"] == false && content["automatic_warnings_approved"] == false) { "Folded candidate schema/calibration policy mismatch" }
        val words = content["vocabulary"] as? List<*> ?: error("Missing vocabulary")
        val identifier = Regex("\\d{5,}|x{3,}\\d|\\d+x{3,}|\\*{2,}", RegexOption.IGNORE_CASE)
        check(words.isNotEmpty() && words.all { it is String && !identifier.containsMatchIn(it) }) { "Identifier-pattern content check failed" }
        check(directory.listFiles()?.map { it.name }?.toSet() == setOf("model.json", "review.properties")) { "Unexpected folded candidate assets" }
        check(!layout.projectDirectory.file("src/main/assets/model.json").asFile.exists()) { "Shared model would contaminate variants" }
    }
}
tasks.matching { it.name == "preLrCalibrated4Build" || it.name == "mergeLrCalibrated4Assets" }
    .configureEach { dependsOn(verifyLrCalibrated4Model) }
// Optional private JVM-only source for auditing the handoff's scorer. Never APK assets.
providers.gradleProperty("candidateParityDir").orNull?.let {
    android.sourceSets.getByName("test").java.srcDir("$it/supplied")
}
val verifyLrCandidateModel by tasks.registering {
    doLast {
        val directory = layout.projectDirectory.dir("src/lrCandidate/assets").asFile
        val model = directory.resolve("model.json")
        val review = directory.resolve("review.properties")
        check(model.isFile && review.isFile) { "LR candidate blocked: model-content review and private assets required; unresolved identifiers must be reviewed." }
        val metadata = Properties().apply { review.inputStream().use { load(it) } }
        check(metadata.getProperty("algorithm") == "lr" && metadata.getProperty("contentReview") == "documented" &&
            metadata.getProperty("contentReviewReference")?.matches(Regex("[A-Za-z0-9_-]{3,100}")) == true) { "Candidate requires an actual model-content evidence reference" }
        val digest = MessageDigest.getInstance("SHA-256").digest(model.readBytes()).joinToString("") { "%02x".format(it) }
        check(digest == metadata.getProperty("sha256")) { "Candidate model changed after content review" }
        check(!metadata.getProperty("modelVersion").isNullOrBlank() &&
            metadata.getProperty("sourceSha256")?.matches(Regex("[0-9a-f]{64}")) == true) { "Candidate requires model version and source identity" }
        val content = JsonSlurper().parse(model) as Map<*, *>
        check(content["schema_version"] == 3 && content["algorithm"] == "lr" &&
            content["model_version"] == metadata.getProperty("modelVersion") &&
            (content["threshold"] as? Number)?.toDouble() == 0.4 &&
            content["threshold_comparison"] == "greater_or_equal" &&
            content["calibration_status"] == "fitted_unvalidated" &&
            content["automatic_warnings_approved"] == false && content["synthetic"] == false) { "Wrong candidate schema or policy" }
        val provenance = content["provenance"] as? Map<*, *>
        check(provenance?.get("source_sha256") == metadata.getProperty("sourceSha256")) { "Candidate source identity mismatch" }
        check(directory.listFiles()?.map { it.name }?.toSet() == setOf("model.json", "review.properties")) { "Unexpected candidate assets" }
        check(!layout.projectDirectory.file("src/main/assets/model.json").asFile.exists()) { "Shared model would contaminate candidate" }
    }
}
tasks.matching { it.name == "preLrCandidateBuild" || it.name == "mergeLrCandidateAssets" }
    .configureEach { dependsOn(verifyLrCandidateModel) }
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
            val reference = metadata.getProperty("reviewReference")
            val preliminary = reference in setOf("preliminary-comparison-20261001", "expanded-comparison-20261005")
            if (preliminary) {
                check(metadata.getProperty("reviewKind") == "automated-pattern-screen" &&
                    metadata.getProperty("humanReview") == "not_recorded") { "State actual automated review, not human acceptance" }
            } else check(metadata.getProperty("manualReview") == "accepted-experimental") { "Local model review is required" }
            val digest = MessageDigest.getInstance("SHA-256").digest(model.readBytes()).joinToString("") { "%02x".format(it) }
            check(digest == metadata.getProperty("sha256")) { "Model changed after review" }
            val content = JsonSlurper().parse(model) as Map<*, *>
            if (content["schema_version"] == 2) {
                check(algorithm == "lr" && digest == "9026c925679f9667b5bd09e34f31dd884cdb72607650d97f9a0708c86fa6bab2") { "Only the reviewed historical LR is supported as schema v2" }
            } else {
                check(content["schema_version"] == 1 && content["algorithm"] == algorithm) { "Export algorithm does not match variant" }
                check(content["synthetic"] == false && content["calibration_evaluated"] == false && content["calibration"] is Map<*, *>) { "Comparison requires an experimental sigmoid export, never a raw-margin percentage or synthetic fixture" }
                if (preliminary) {
                    val protocol = rootProject.file(if (reference == "expanded-comparison-20261005")
                        "docs/expanded-comparison-protocol-20261005.md" else "docs/preliminary-comparison-protocol-20261001.md")
                    val protocolHash = MessageDigest.getInstance("SHA-256").digest(protocol.readBytes()).joinToString("") { "%02x".format(it) }
                    check(metadata.getProperty("protocolSha256") == protocolHash && content["protocol_sha256"] == protocolHash &&
                        content["evaluation_status"] == "preliminary_retrospective" && content["label_status"] == "inherited_unconfirmed" &&
                        content["model_version"] == metadata.getProperty("modelVersion") && content["automatic_warnings_approved"] == false &&
                        content["score_transform"] == "fitted_sigmoid" && content["calibration_fit_partition"] == "calibration" &&
                        content["threshold_fit_partition"] == "validation") { "Preliminary protocol/identity mismatch" }
                    val words = content["vocabulary"] as? List<*> ?: error("Missing vocabulary")
                    check(words.isNotEmpty() && words.all { it is String && it.matches(Regex("[a-z]+")) }) { "Vocabulary content check failed" }
                }
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
    add("mbertQuantizedImplementation", "com.microsoft.onnxruntime:onnxruntime-android:1.22.0")
    add("mbertImplementation", "com.microsoft.onnxruntime:onnxruntime-android:1.22.0")
    implementation(platform("androidx.compose:compose-bom:2025.12.01"))
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.appcompat:appcompat:1.7.1")
    implementation("dev.chrisbanes.haze:haze:1.7.2")
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
