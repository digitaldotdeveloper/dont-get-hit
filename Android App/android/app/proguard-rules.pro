# Capacitor finds its plugins, its bridge and its JavaScript interfaces by
# reflection, so it is kept whole. R8 still cuts AndroidX and everything else
# down to what is called -- that is where the size is.
-keep class com.getcapacitor.** { *; }
-keep class org.apache.cordova.** { *; }
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
-keepattributes *Annotation*,Signature,InnerClasses,EnclosingMethod

# Readable stack traces: Play Console de-obfuscates with the mapping file that
# goes up inside the AAB (and build.mjs copies to dist/).
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile
