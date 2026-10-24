/* Native regression: the bottom dock has only the capsule's visible bounds.
 * Map an offscreen unmanaged popup; never move the pointer or start a model. */
#include <webkit2/webkit2.h>
#include <gdk/gdkx.h>
#include <X11/extensions/shape.h>
#include <stdio.h>
static GtkWidget *window;
static int stage, result = 1;
static gboolean matches(GdkWindow *gdk, int kind, int width, int height) {
    Display *display = GDK_WINDOW_XDISPLAY(gdk);
    XSync(display, False);
    int count, ordering;
    XRectangle *rects = XShapeGetRectangles(display, GDK_WINDOW_XID(gdk), kind, &count, &ordering);
    gboolean ok = width ? count == 1 && rects[0].width == width && rects[0].height == height : count == 0;
    XFree(rects); return ok;
}
static void change(WebKitWebView *view, const char *js) {
    webkit_web_view_evaluate_javascript(view, js, -1, NULL, NULL, NULL, NULL, NULL);
}
static gboolean check_shape(gpointer data) {
    WebKitWebView *view = WEBKIT_WEB_VIEW(data);
    const char *title = webkit_web_view_get_title(view);
    if (!title || !g_str_has_prefix(title, "Coucou Flow | ")) return G_SOURCE_CONTINUE;
    GdkWindow *gdk = gtk_widget_get_window(window);
    if (!stage && matches(gdk, ShapeInput, 44, 8)) {
        if (!matches(gdk, ShapeBounding, 44, 8)) return G_SOURCE_CONTINUE;
        /* The native page's padded hover region must not enlarge the handle. */
        cairo_rectangle_int_t padded = {212, 144, 96, 26};
        cairo_region_t *region = cairo_region_create_rectangle(&padded);
        gdk_window_input_shape_combine_region(gdk, region, 0, 0); cairo_region_destroy(region);
        if (!matches(gdk, ShapeInput, 44, 8)) goto fail;
        stage = 1;
        change(view, "Object.assign(document.querySelector('.capsule').style,{left:'185px',top:'134px',width:'150px',height:'34px'})");
    } else if (stage == 1 && matches(gdk, ShapeInput, 150, 34)) {
        if (!matches(gdk, ShapeBounding, 150, 34)) return G_SOURCE_CONTINUE;
        stage = 2; change(view, "document.querySelector('.capsule').remove()");
    } else if (stage == 2 && matches(gdk, ShapeInput, 0, 0)) {
        if (!matches(gdk, ShapeBounding, 0, 0)) return G_SOURCE_CONTINUE;
        result = 0; puts("Flow: exact handle, padded reset rejected, toolbar bounds, empty when absent"); gtk_main_quit();
    }
    return G_SOURCE_CONTINUE;
fail:
    fprintf(stderr, "Unexpected Flow shape at stage %d\n", stage); gtk_main_quit(); return G_SOURCE_REMOVE;
}
static gboolean timeout(gpointer data) { fputs("Flow shape timeout\n", stderr); gtk_main_quit(); return G_SOURCE_REMOVE; }
int main(int argc, char **argv) {
    gtk_init(&argc, &argv);
    window = gtk_window_new(GTK_WINDOW_POPUP); gtk_window_set_default_size(GTK_WINDOW(window), 520, 170);
    WebKitWebView *view = WEBKIT_WEB_VIEW(webkit_web_view_new());
    gtk_container_add(GTK_CONTAINER(window), GTK_WIDGET(view)); gtk_widget_realize(window);
    gdk_window_resize(gtk_widget_get_window(window), 520, 170);
    gtk_window_move(GTK_WINDOW(window), -10000, -10000);
    gtk_widget_show_all(window);
    webkit_web_view_load_html(view, "<div id='pill'><div class='capsule' style='position:absolute;left:238px;top:160px;width:44px;height:8px'></div></div>", "tauri://localhost/pill.html");
    g_timeout_add(40, check_shape, view);
    g_timeout_add_seconds(8, timeout, NULL); gtk_main(); gtk_widget_destroy(window); return result;
}
