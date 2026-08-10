import java.util.Properties
import java.io.FileInputStream

plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

// Release signing is read from environment variables when present, otherwise it
// falls back to the local (git-ignored) `key.properties` file. Secrets must
// never be hard-coded here or committed to version control.
val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("key.properties")
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(FileInputStream(keystorePropertiesFile))
}

val envOrNull = { name: String -> System.getenv(name) }
fun secret(name: String, localName: String): String? =
    envOrNull(name) ?: keystoreProperties.getProperty(localName)

android {
    namespace = "com.kisanai.app"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        applicationId = "com.kisanai.app"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        create("release") {
            val storeFileValue = secret("KISANAI_STORE_FILE", "storeFile")
            if (storeFileValue != null) {
                storeFile = rootProject.file(storeFileValue)
                storePassword = secret("KISANAI_STORE_PASSWORD", "storePassword")
                keyAlias = secret("KISANAI_KEY_ALIAS", "keyAlias")
                keyPassword = secret("KISANAI_KEY_PASSWORD", "keyPassword")
            }
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = true
            isShrinkResources = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
