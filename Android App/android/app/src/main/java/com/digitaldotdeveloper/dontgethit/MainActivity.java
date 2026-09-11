package com.digitaldotdeveloper.dontgethit;

import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.webkit.WebSettings;
import android.webkit.WebView;
import androidx.activity.OnBackPressedCallback;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;
import com.getcapacitor.BridgeActivity;

/**
 * DON'T GET HIT is a landscape, full-screen, hold-to-fly canvas. Capacitor
 * supplies the WebView and serves www/ out of the APK; this adds what a game
 * needs from its window. The page's half of it is src/shim.js.
 */
public class MainActivity extends BridgeActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // A long run is one finger held still; the screen must not time out under it.
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        if (bridge == null) return; // no usable WebView: Capacitor has shown its own page

        WebView web = bridge.getWebView();
        WebSettings settings = web.getSettings();
        // The phone's font-size setting must not resize a HUD laid out in vmin.
        settings.setTextZoom(100);
        // Holding IS the control: a long press must not buzz, select or open a
        // menu, and the page must never rubber-band under a thumb.
        web.setHapticFeedbackEnabled(false);
        web.setLongClickable(false);
        web.setOnLongClickListener(v -> true);
        web.setOverScrollMode(View.OVER_SCROLL_NEVER);
        web.setVerticalScrollBarEnabled(false);
        web.setHorizontalScrollBarEnabled(false);

        // Back closes an open panel (the page decides, see __dghBack in the shim);
        // anywhere else it sends the app to the background with the run intact.
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                WebView w = bridge.getWebView();
                if (w.canGoBack()) {
                    w.goBack();
                    return;
                }
                w.evaluateJavascript("window.__dghBack ? window.__dghBack() : false", used -> {
                    if (!"true".equals(used)) moveTaskToBack(true);
                });
            }
        });
        immersive();
    }

    /** Full screen, bars a swipe away and gone again on their own. */
    private void immersive() {
        WindowInsetsControllerCompat bars = WindowCompat.getInsetsController(getWindow(), getWindow().getDecorView());
        bars.setSystemBarsBehavior(WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
        bars.hide(WindowInsetsCompat.Type.systemBars());
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) immersive(); // a dialog, the shade or a return from recents brings the bars back
    }

    /* Capacitor does not pause its WebView with the activity, so a backgrounded
       game kept its music playing. Pausing the WebView makes the page hidden --
       the game already suspends its sound effects and releases the thrust on
       that -- and the events reach the shim, which pauses the <audio> music. */
    @Override
    public void onResume() {
        super.onResume();
        immersive();
        if (bridge != null) {
            bridge.getWebView().onResume();
            page("dgh:resume");
        }
    }

    @Override
    public void onPause() {
        if (bridge != null) {
            page("dgh:pause");
            bridge.getWebView().onPause();
        }
        super.onPause();
    }

    private void page(String event) {
        bridge.getWebView().evaluateJavascript("window.dispatchEvent(new Event('" + event + "'))", null);
    }
}
