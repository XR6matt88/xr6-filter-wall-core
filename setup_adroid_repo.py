cat << 'EOF' > setup_android_repo.py
import os
import zipfile

base = "xr6-filter-wall-android"
dirs = [
    f"{base}/.github/workflows",
    f"{base}/app/src/main/java/com/xr6labs/filterwall",
    f"{base}/app/src/main/python",
    f"{base}/app/src/main/res/values",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# 1. GitHub Actions Workflow (Kompilasi APK Awan Automatik)
workflow_yml = """name: Build XR6 Android APK

on:
  push:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Setup Android SDK
        uses: android-actions/setup-android@v3

      - name: Install Gradle & Build Debug APK
        run: |
          sudo apt-get update && sudo apt-get install -y gradle
          gradle wrapper --gradle-version 8.4
          chmod +x gradlew
          ./gradlew assembleDebug

      - name: Upload APK Artifact
        uses: actions/upload-artifact@v4
        with:
          name: XR6-FilterWall-APK
          path: app/build/outputs/apk/debug/app-debug.apk
"""
with open(f"{base}/.github/workflows/build-apk.yml", "w", encoding="utf-8") as f:
    f.write(workflow_yml)

# 2. Root build.gradle.kts
root_gradle = """plugins {
    id("com.android.application") version "8.2.0" apply false
    id("org.jetbrains.kotlin.android") version "1.9.20" apply false
    id("com.chaquo.python") version "15.0.1" apply false
}
"""
with open(f"{base}/build.gradle.kts", "w", encoding="utf-8") as f:
    f.write(root_gradle)

# 3. settings.gradle.kts
settings_gradle = """pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "XR6FilterWall"
include(":app")
"""
with open(f"{base}/settings.gradle.kts", "w", encoding="utf-8") as f:
    f.write(settings_gradle)

# 4. gradle.properties
gradle_props = """org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
kotlin.code.style=official
android.nonTransitiveRClass=true
"""
with open(f"{base}/gradle.properties", "w", encoding="utf-8") as f:
    f.write(gradle_props)

# 5. app/build.gradle.kts
app_gradle = """plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python")
}

android {
    namespace = "com.xr6labs.filterwall"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.xr6labs.filterwall"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"

        ndk {
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
        python {
            version = "3.11"
            pip {
                install("filter-wall-core")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
}
"""
with open(f"{base}/app/build.gradle.kts", "w", encoding="utf-8") as f:
    f.write(app_gradle)

# 6. AndroidManifest.xml
manifest_xml = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />

    <application
        android:allowBackup="true"
        android:label="XR6 Filter Wall"
        android:supportsRtl="true"
        android:theme="@style/Theme.MaterialComponents.DayNight.DarkActionBar">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <service
            android:name=".FilterVpnService"
            android:permission="android.permission.BIND_VPN_SERVICE"
            android:exported="false">
            <intent-filter>
                <action android:name="android.net.VpnService" />
            </intent-filter>
        </service>
    </application>
</manifest>
"""
with open(f"{base}/app/src/main/AndroidManifest.xml", "w", encoding="utf-8") as f:
    f.write(manifest_xml)

# 7. MainActivity.kt (Antaramuka Pengguna dengan Butang Hidup/Mati)
main_activity = """package com.xr6labs.filterwall

import android.app.Activity
import android.content.Intent
import android.net.VpnService
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class MainActivity : AppCompatActivity() {
    private lateinit var statusText: TextView
    private var isActive = false

    private val vpnLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            startVpnService()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(48, 48, 48, 48)
        }

        val title = TextView(this).apply {
            text = "XR6 - FILTER WALL"
            textSize = 24f
            gravity = Gravity.CENTER
        }

        statusText = TextView(this).apply {
            text = "Status: Perlindungan Dimatikan"
            textSize = 16f
            gravity = Gravity.CENTER
            setPadding(0, 24, 0, 48)
        }

        val toggleBtn = Button(this).apply {
            text = "Hidupkan / Matikan Penapis"
            setOnClickListener {
                if (!isActive) {
                    val intent = VpnService.prepare(this@MainActivity)
                    if (intent != null) {
                        vpnLauncher.launch(intent)
                    } else {
                        startVpnService()
                    }
                } else {
                    stopService(Intent(this@MainActivity, FilterVpnService::class.java))
                    isActive = false
                    statusText.text = "Status: Perlindungan Dimatikan"
                }
            }
        }

        layout.addView(title)
        layout.addView(statusText)
        layout.addView(toggleBtn)
        setContentView(layout)
    }

    private fun startVpnService() {
        startService(Intent(this, FilterVpnService::class.java))
        isActive = true
        statusText.text = "Status: Aktif (Enjin 3-Lapisan Berjalan)"
    }
}
"""
with open(f"{base}/app/src/main/java/com/xr6labs/filterwall/MainActivity.kt", "w", encoding="utf-8") as f:
    f.write(main_activity)

# 8. FilterVpnService.kt (Terowong Rangkaian + Penghurai SNI TLS)
vpn_service = """package com.xr6labs.filterwall

import android.content.Intent
import android.net.VpnService
import android.os.ParcelFileDescriptor
import com.chaquo.python.Python
import java.io.FileInputStream
import java.io.FileOutputStream
import java.nio.ByteBuffer

class FilterVpnService : VpnService() {
    private var vpnInterface: ParcelFileDescriptor? = null
    private var isRunning = false

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (!isRunning) {
            isRunning = true
            val builder = Builder()
                .setSession("XR6 Filter Wall")
                .addAddress("10.0.0.2", 32)
                .addRoute("0.0.0.0", 0)
                .addDnsServer("1.1.1.1")
            vpnInterface = builder.establish()
            Thread { processPackets() }.start()
        }
        return START_STICKY
    }

    private fun processPackets() {
        val py = Python.getInstance()
        val bridge = py.getModule("bridge")
        val fd = vpnInterface?.fileDescriptor ?: return
        val input = FileInputStream(fd)
        val output = FileOutputStream(fd)
        val buffer = ByteBuffer.allocate(32767)

        while (isRunning) {
            val length = try { input.read(buffer.array()) } catch (e: Exception) { -1 }
            if (length > 0) {
                val sni = extractTlsSni(buffer.array(), length)
                val result = bridge.callAttr(
                    "inspect_from_android",
                    "pkt-${System.nanoTime()}",
                    sni,
                    sni
                ).asMap()

                val permitted = result[py.builtins.callAttr("str", "permitted")]?.toBoolean() ?: true
                if (permitted) {
                    output.write(buffer.array(), 0, length)
                }
                buffer.clear()
            }
        }
    }

    private fun extractTlsSni(packet: ByteArray, length: Int): String {
        if (length < 44) return ""
        val ipHeaderLen = (packet[0].toInt() and 0x0F) * 4
        if (packet[9].toInt() != 6 || length < ipHeaderLen + 20) return ""
        val tcpHeaderLen = ((packet[ipHeaderLen + 12].toInt() ushr 4) and 0x0F) * 4
        val payloadOffset = ipHeaderLen + tcpHeaderLen
        if (length <= payloadOffset + 43 || packet[payloadOffset].toInt() != 0x16) return ""

        var pos = payloadOffset + 43
        if (pos >= length) return ""
        val sessionIdLen = packet[pos].toInt() and 0xFF
        pos += 1 + sessionIdLen
        if (pos + 2 >= length) return ""
        val cipherSuitesLen = ((packet[pos].toInt() and 0xFF) shl 8) or (packet[pos + 1].toInt() and 0xFF)
        pos += 2 + cipherSuitesLen
        if (pos >= length) return ""
        val compMethodsLen = packet[pos].toInt() and 0xFF
        pos += 1 + compMethodsLen
        if (pos + 2 >= length) return ""
        val extensionsLen = ((packet[pos].toInt() and 0xFF) shl 8) or (packet[pos + 1].toInt() and 0xFF)
        pos += 2
        val end = minOf(pos + extensionsLen, length)

        while (pos + 4 <= end) {
            val extType = ((packet[pos].toInt() and 0xFF) shl 8) or (packet[pos + 1].toInt() and 0xFF)
            val extLen = ((packet[pos + 2].toInt() and 0xFF) shl 8) or (packet[pos + 3].toInt() and 0xFF)
            pos += 4
            if (extType == 0x0000 && pos + 5 <= end) {
                val nameLen = ((packet[pos + 3].toInt() and 0xFF) shl 8) or (packet[pos + 4].toInt() and 0xFF)
                if (pos + 5 + nameLen <= end) {
                    return String(packet, pos + 5, nameLen, Charsets.UTF_8)
                }
            }
            pos += extLen
        }
        return ""
    }

    override fun onDestroy() {
        isRunning = false
        vpnInterface?.close()
        super.onDestroy()
    }
}
"""
with open(f"{base}/app/src/main/java/com/xr6labs/filterwall/FilterVpnService.kt", "w", encoding="utf-8") as f:
    f.write(vpn_service)

# 9. bridge.py (Jambatan ke Pakej PyPI filter-wall-core)
bridge_py = """import asyncio
from filter_wall_core import NetworkPipeline, NetworkPacket, PacketStatus

pipeline = NetworkPipeline()

def inspect_from_android(packet_id: str, domain: str, sni: str) -> dict:
    async def _run():
        pkt = NetworkPacket(
            packet_id=packet_id,
            domain=domain if domain else None,
            sni=sni if sni else None
        )
        res = await pipeline.inspect_packet(pkt)
        return {
            "permitted": res.status == PacketStatus.PERMITTED,
            "status": res.status.value,
            "reason": res.reason
        }
    return asyncio.run(_run())
"""
with open(f"{base}/app/src/main/python/bridge.py", "w", encoding="utf-8") as f:
    f.write(bridge_py)

# 10. README.md
readme = """# XR6 - Filter Wall (Android Client)
Aplikasi Android natif dengan terowong `VpnService` dan jambatan Chaquopy ke enjin `filter-wall-core` (PyPI).
"""
with open(f"{base}/README.md", "w", encoding="utf-8") as f:
    f.write(readme)

# Cipta fail ZIP di folder Download telefon
zip_out = os.path.expanduser("~/storage/downloads/xr6-filter-wall-android.zip")
os.makedirs(os.path.dirname(zip_out), exist_ok=True)
with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(base):
        for file in files:
            full_path = os.path.join(root, file)
            z.write(full_path, os.path.relpath(full_path, base))

print(f"BERJAYA: Folder '{base}' dan fail '{zip_out}' telah dijana!")
EOF
python3 setup_android_repo.py
