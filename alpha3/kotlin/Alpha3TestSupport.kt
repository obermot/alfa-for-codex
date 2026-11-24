package com.nezabudka.testharness

import android.app.Instrumentation
import android.content.Context
import android.os.ParcelFileDescriptor
import android.util.AtomicFile
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.layout.LayoutCoordinates
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.ComposeTestRule
import androidx.test.uiautomator.UiDevice
import java.io.File
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executor
import java.util.concurrent.TimeUnit
import org.json.JSONObject

/** Test-only infrastructure. Never linked into the application APK. */
internal object Alpha3TestSupport {
    fun clearPersistedSession(context: Context) {
        // onPause writes asynchronously. Drain its real writer before deleting all AtomicFile variants.
        val writerField=FinalUiSessionStore::class.java.getDeclaredField("writer").apply { isAccessible=true }
        val drained=CountDownLatch(1)
        (writerField.get(null) as Executor).execute { drained.countDown() }
        check(drained.await(10,TimeUnit.SECONDS)) { "UI-session writer did not drain" }
        val file=File(context.noBackupFilesDir,"last-ui-session-v1")
        AtomicFile(file).delete()
        check(listOf(file,File(file.path+".bak"),File(file.path+".new")).none {it.exists()}) { "Persisted UI session still exists" }
    }

    private fun shell(inst: Instrumentation, command: String): String = ParcelFileDescriptor.AutoCloseInputStream(
        inst.uiAutomation.executeShellCommand(command)).bufferedReader().use {it.readText()}

    fun capture(inst: Instrumentation, ui: ComposeTestRule, label: String) {
        val context=inst.targetContext
        val directory=File(context.getExternalFilesDir(null),"device-evidence").apply {check(isDirectory || mkdirs())}
        fun file(suffix:String)=File(directory,label+suffix)
        val errors=mutableListOf<String>()
        runCatching {
            val bitmap=checkNotNull(inst.uiAutomation.takeScreenshot()) { "UiAutomation returned no screenshot" }
            try {file(".full.png").outputStream().use {check(bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG,100,it))}}
            finally {bitmap.recycle()}
        }.onFailure {errors.add("screenshot: $it")}
        runCatching {UiDevice.getInstance(inst).dumpWindowHierarchy(file(".window.xml"))}.onFailure {errors.add("hierarchy: $it")}
        file(".semantics-full.txt").writeText(runCatching {ui.onRoot(useUnmergedTree=true).printToString()}.getOrElse {"No root: $it"})
        for((suffix,command) in listOf(".windows.txt" to "dumpsys window windows", ".activities.txt" to "dumpsys activity activities",
            ".audio.txt" to "dumpsys audio", ".alarms.txt" to "dumpsys alarm", ".display.txt" to "wm size; wm density; settings get system font_scale; cmd uimode night")) {
            runCatching {file(suffix).writeText(shell(inst,command))}.onFailure {errors.add("$suffix: $it")}
        }
        file(".environment.json").writeText(JSONObject().put("sdk",android.os.Build.VERSION.SDK_INT)
            .put("model",android.os.Build.MODEL).put("densityDpi",context.resources.displayMetrics.densityDpi)
            .put("fontScale",context.resources.configuration.fontScale).put("captureErrors",errors.joinToString("\n")).toString(2))
        file(".capture-status.txt").writeText(if(errors.isEmpty())"OK" else errors.joinToString("\n"))
    }

    fun toggleForLabel(ui: ComposeTestRule, label: String) {
        val text=ui.onNodeWithText(label,useUnmergedTree=true).fetchSemanticsNode()
        val scale=ui.onRoot().fetchSemanticsNode().boundsInRoot.width/1080f
        var coordinates: LayoutCoordinates?=text.layoutInfo.coordinates
        while(coordinates!=null && !(kotlin.math.abs(coordinates.size.width-1000*scale)<3 &&
                    kotlin.math.abs(coordinates.size.height-FinalCorelVisualTokens.ListCardH*scale)<3)) coordinates=coordinates.parentLayoutCoordinates
        val card=checkNotNull(coordinates) {"No measured card around $label"}
        val origin=card.localToRoot(Offset.Zero)
        val candidates=ui.onAllNodes(hasClickAction(),useUnmergedTree=true).fetchSemanticsNodes().filter {
            val b=it.boundsInRoot
            b.left>=origin.x+600*scale && b.right<=origin.x+840*scale &&
                b.top>=origin.y-1 && b.bottom<=origin.y+card.size.height+1 && b.height>150*scale
        }
        check(candidates.size==1) {"Expected one measured switch for $label, found ${candidates.size}"}
        val target=candidates.single()
        ui.onNode(SemanticsMatcher("measured switch for $label") {it.id==target.id},useUnmergedTree=true)
            .performTouchInput {click()}
    }

    fun tapRepeatMode(ui: ComposeTestRule,label:String) {
        val heading=ui.onNodeWithText("Повторять напоминание?",useUnmergedTree=true).fetchSemanticsNode().boundsInRoot
        val choices=ui.onAllNodesWithText(label,substring=false,useUnmergedTree=true).fetchSemanticsNodes().filter {it.boundsInRoot.top>heading.bottom}
        check(choices.size==1) {"Ambiguous repeat mode $label: ${choices.size}"}
        val target=choices.single()
        ui.onNode(SemanticsMatcher("repeat choice $label") {it.id==target.id},useUnmergedTree=true).performTouchInput {click()}
    }
}
