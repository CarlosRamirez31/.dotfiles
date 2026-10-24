/* Exercises the installed asynchronous WebKit -> Python -> CLI JSON bridge.
 * No window is shown. `agents --json` cannot invoke a model. */
#include <webkit2/webkit2.h>
#include <stdio.h>
#include <string.h>
static int result = 1;
static void title_changed(WebKitWebView *view, GParamSpec *spec, gpointer data) {
    const char *title = webkit_web_view_get_title(view);
    if (!title) return;
    if (strcmp(title, "bridge-ok") == 0) {
        result = 0; puts("Native WebKit/Python/Agent Hub JSON round trip passed"); gtk_main_quit();
    } else if (g_str_has_prefix(title, "bridge-error:")) {
        fprintf(stderr, "%s\n", title); gtk_main_quit();
    }
}
static gboolean timeout(gpointer data) { fputs("Native bridge timeout\n", stderr); gtk_main_quit(); return G_SOURCE_REMOVE; }
int main(int argc, char **argv) {
    gtk_init(&argc, &argv);
    GtkWidget *window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    WebKitWebView *view = WEBKIT_WEB_VIEW(webkit_web_view_new());
    gtk_container_add(GTK_CONTAINER(window), GTK_WIDGET(view));
    g_signal_connect(view, "notify::title", G_CALLBACK(title_changed), NULL);
    webkit_web_view_load_html(view,
        "<html><body><script>window.webkit.messageHandlers.coucouAgentHub.postMessage({action:'agents'})"
        ".then(r=>{document.title=r.ok&&Array.isArray(r.items)?'bridge-ok':'bridge-error:'+JSON.stringify(r)})"
        ".catch(e=>{document.title='bridge-error:'+e.message})</script></body></html>", "tauri://localhost/");
    g_timeout_add_seconds(10, timeout, NULL);
    gtk_main(); gtk_widget_destroy(window); return result;
}
