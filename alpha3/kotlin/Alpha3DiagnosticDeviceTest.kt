package com.nezabudka.testharness

import android.graphics.Bitmap
import androidx.compose.ui.test.*
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.uiautomator.By
import androidx.test.uiautomator.Until
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

/** Extra diagnostics; the 78 original Android methods run independently and are never replaced. */
@RunWith(AndroidJUnit4::class)
class Alpha3DiagnosticDeviceTest : FinalDeviceFixture() {
    private fun evidence(label:String)=Alpha3TestSupport.capture(inst,ui,label)
    @Test fun englishLanguageAndDirtyNoteSurviveActivityRecreationAndRelaunch() {
        val id=futureDaily("Original user text — не переводить")
        val originalLocale=java.util.Locale.getDefault()
        val prefs=app.getSharedPreferences("nezabudka_final_prefs",0)
        prefs.edit().putString("settings_voice","Мужской").commit()
        FinalUiLanguage.select(app,FinalUiLanguage.ENGLISH)
        androidx.test.core.app.ActivityScenario.launch<FinalMainActivity>(
            android.content.Intent(app,FinalMainActivity::class.java)).use { scenario ->
            text("Current reminders");tap("Original user text — не переводить");tap("Add a note")
            ui.onNode(hasSetTextAction()).performTextInput("Unsaved draft — код512")
            scenario.recreate()
            text("Done")
            ui.onNode(hasSetTextAction()).assertTextEquals("Unsaved draft — код512")
            assertTrue(reminder(id)?.note.isNullOrBlank())
            assertEquals(FinalUiLanguage.ENGLISH,FinalUiLanguage.read(app))
            evidence("english-dirty-note-after-recreation")
            tap("Done")
            await("English note committed only by Done") {reminder(id)?.note=="Unsaved draft — код512"}
            text("Editing")
        }
        // A new Activity reads persisted language; this is not a process-death claim.
        launchMain();text("Editing");tap("Unsaved draft — код512");text("Done")
        ui.onNode(hasSetTextAction()).assertTextEquals("Unsaved draft — код512")
        assertEquals(FinalUiLanguage.ENGLISH,FinalUiLanguage.read(app))
        assertEquals("Original user text — не переводить",reminder(id)?.text)
        assertEquals("Мужской",prefs.getString("settings_voice",null))
        assertEquals(originalLocale,java.util.Locale.getDefault())
        evidence("english-note-after-new-activity-launch")
    }
    private fun menu() {
        val b=ui.onNodeWithText("Все").fetchSemanticsNode().boundsInRoot
        ui.onRoot().performTouchInput { click(androidx.compose.ui.geometry.Offset(b.right+115*b.width/170,b.center.y)) }
    }

    @Test fun F01_androidAccessibilityCanFindAndActivateRemindAgain() {
        val (_,e)=seed();full(e)
        assertEquals(EventState.ACKNOWLEDGED,event(e)?.state)
        evidence("F01-before-accessibility")
        assertTrue("Real Android accessibility: Remind Again",device.wait(Until.hasObject(By.desc("Напомнить снова")),10_000))
        assertTrue("Real Android accessibility: Close",device.wait(Until.hasObject(By.desc("Закрыть")),10_000))
        device.findObject(By.desc("Напомнить снова")).click()
        FinalSnoozeChoices.options.forEach {text(it.label)}
        evidence("F01-after-accessibility-action")
        assertEquals(EventState.ACKNOWLEDGED,event(e)?.state)
        assertFalse(FinalAlarmSignalPlayer.isActive(e))
    }

    @Test fun F03_alarmDeliveryHasVisibleFocusedInteractiveCompactWindow() {
        main()
        val id=runBlocking {service.createOneShot("F03 компактное окно",System.currentTimeMillis()+3_000)}
        val e=runBlocking {dao.eventsForReminder(id).single().id}
        await("F03 actual AlarmManager delivery",20_000) {event(e)?.state==EventState.FIRING}
        evidence("F03-delivery-window-focus")
        await("F03 compact window actually focused",15_000) {resumed(FinalCompactAlarmActivity::class.java)}
        ui.onRoot().assertIsDisplayed().performTouchInput {click(center)}
        text("Напомнить снова")
        await("F03 user opening acknowledges") {event(e)?.state==EventState.ACKNOWLEDGED}
        evidence("F03-after-user-open")
        assertFalse(FinalAlarmSignalPlayer.isActive(e))
    }

    @Test fun F11_noRepeatSelectionPersistsAndSurvivesRecreation() {
        val id=futureDaily("F11 режим повторения")
        main();tap("F11 режим повторения");tap("Повторять напоминание?")
        evidence("F11-daily-before-selection")
        Alpha3TestSupport.tapRepeatMode(ui,"Ежедневно")
        text("Не повторять")
        evidence("F11-mode-options")
        Alpha3TestSupport.tapRepeatMode(ui,"Не повторять")
        await("F11 ONE_SHOT persisted") {reminder(id)?.mode==ReminderMode.ONE_SHOT}
        assertTrue(runBlocking {dao.scheduleSlots(id).isNotEmpty()})
        recreateCurrent();text("Не повторять")
        assertEquals(ReminderMode.ONE_SHOT,reminder(id)?.mode)
        evidence("F11-one-shot-after-recreation")
    }

    @Test fun F28_exportActualIconBeforeOriginalPaletteAndSafeAreaAssertions() {
        val icon=app.applicationInfo.loadIcon(app.packageManager)
        assertTrue(icon is android.graphics.drawable.AdaptiveIconDrawable)
        val pixels=Bitmap.createBitmap(216,216,Bitmap.Config.ARGB_8888)
        icon.setBounds(0,0,216,216);icon.draw(android.graphics.Canvas(pixels))
        val directory=File(app.getExternalFilesDir(null),"device-evidence").apply {check(isDirectory || mkdirs())}
        File(directory,"F28-actual-icon.png").outputStream().use {check(pixels.compress(Bitmap.CompressFormat.PNG,100,it))}
        val counts=mutableMapOf<Int,Int>()
        for(y in 0 until pixels.height) for(x in 0 until pixels.width) {
            val c=pixels.getPixel(x,y);counts[c]=(counts[c]?:0)+1
        }
        File(directory,"F28-icon-colours.json").writeText(org.json.JSONObject(counts.mapKeys {it.key.toUInt().toString(16)}).toString(2))
        pixels.recycle()
        val foreground=app.getDrawable(R.drawable.ic_launcher_foreground)!!
        val safe=Bitmap.createBitmap(108,108,Bitmap.Config.ARGB_8888)
        foreground.setBounds(0,0,108,108);foreground.draw(android.graphics.Canvas(safe))
        val outside=mutableListOf<String>()
        for(y in 0 until 108) for(x in 0 until 108)
            if(android.graphics.Color.alpha(safe.getPixel(x,y))>0 && (x !in 21..86 || y !in 21..86))outside.add("$x,$y")
        File(directory,"F28-safe-area.txt").writeText("outsidePixels=${outside.size}\n"+outside.take(200).joinToString("\n"))
        safe.recycle()
        // The current approved PDF and owner confirmation require the white logo.
        for(c in listOf(0xFF008CA1.toInt(),0xFFFFFFFF.toInt(),0xFF00AEC9.toInt()))
            assertTrue("Original owner palette missing ${c.toUInt().toString(16)}",(counts[c]?:0)>50)
        assertTrue("Logo outside original adaptive safe area",outside.isEmpty())
    }

    @Test fun F37_firstRunDrawsUsableNamePageWithoutSeparateLogoPage() {
        app.getSharedPreferences("nezabudka_final_prefs",0).edit().clear().putBoolean("setup_done",false).commit()
        Alpha3TestSupport.clearPersistedSession(app)
        val directory=File(app.getExternalFilesDir(null),"device-evidence").apply {check(isDirectory || mkdirs())}
        val recording=inst.uiAutomation.executeShellCommand("screenrecord --time-limit 8 ${File(directory,"F37-startup.mp4").absolutePath}")
        try {
            launchMain();text("Как к вам обращаться?")
            ui.onNodeWithText("Как к вам обращаться?").assertIsDisplayed()
            ui.onNodeWithText("Пропустить").assertIsDisplayed()
            evidence("F37-first-usable-onboarding")
            ui.onNode(hasSetTextAction()).performTextInput("Проверка Alpha 3")
            tap("Далее");text("Разрешите приложению:")
            evidence("F37-after-first-action")
        } finally {
            val output=android.os.ParcelFileDescriptor.AutoCloseInputStream(recording).bufferedReader().use {it.readText()}
            File(directory,"F37-screenrecord.txt").writeText(output)
        }
    }

    @Test fun geometryImeAndTheme() {
        val id=futureDaily("Адаптивность: длинный текст напоминания для проверки двух строк")
        main();menu();tap("Оформление")
        ui.onNodeWithText("Тёмная тема").assertIsEnabled().performTouchInput {click()}
        await("approved dark theme persisted") {app.getSharedPreferences("nezabudka_final_prefs",0).getString("appearance",null)=="dark"}
        evidence("matrix-approved-dark-theme")
        ui.onNodeWithText("Светлая тема").assertIsEnabled().performTouchInput {click()}
        await("light theme restored") {app.getSharedPreferences("nezabudka_final_prefs",0).getString("appearance",null)=="light"}
        evidence("matrix-approved-light-theme")
        device.pressBack();text("Настройки");device.pressBack();text("Текущие напоминания")
        tap("Адаптивность: длинный текст напоминания для проверки двух строк")
        val back=ui.onNodeWithContentDescription("Назад").fetchSemanticsNode().boundsInRoot
        tap("Адаптивность: длинный текст напоминания для проверки двух строк")
        val editorBack=ui.onNodeWithContentDescription("Назад").fetchSemanticsNode().boundsInRoot
        assertEquals("Editor width must not shrink",back.width,editorBack.width,2f)
        val field=ui.onNode(hasSetTextAction())
        field.performClick();field.performTextInput(". Дополнительная строка для проверки клавиатуры.")
        await("Real IME shown") {keyboardTop()!=null}
        val done=ui.onNodeWithText("Готово").assertIsDisplayed().fetchSemanticsNode().boundsInRoot
        assertTrue("Done overlaps actual IME",done.bottom<=keyboardTop()!!+2)
        evidence("matrix-real-ime-with-long-text")
        tap("Готово")
        await("Matrix text persisted") {reminder(id)?.text?.contains("Дополнительная строка")==true}
    }
}
