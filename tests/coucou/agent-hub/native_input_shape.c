/* Hidden native fixture: validates actual X11 ShapeInput, without moving the mouse. */
#include <webkit2/webkit2.h>
#include <gdk/gdkx.h>
#include <X11/extensions/shape.h>
#include <stdio.h>
static GtkWidget *window;
static int stage, result=1;
static void title_changed(WebKitWebView *view, GParamSpec *p, gpointer data) {
    const char *title=webkit_web_view_get_title(view);
    if (!title || !g_str_has_prefix(title,"Coucou Island | ")) return;
    GdkWindow *gdk=gtk_widget_get_window(window);
    Display *display=GDK_WINDOW_XDISPLAY(gdk);
    XSync(display,False);
    int count=0,ordering=0;
    XRectangle *rects=XShapeGetRectangles(display,GDK_WINDOW_XID(gdk),ShapeInput,&count,&ordering);
    XFree(rects);
    if (stage==0 && count>0) {
        stage=1;
        webkit_web_view_evaluate_javascript(view,"document.title='Coucou Island | compact | 288 | 32'",-1,NULL,NULL,NULL,NULL,NULL);
    } else if(stage==1 && count==0) {
        /* Reproduce a stale native region reset while the island remains invisible. */
        gdk_window_input_shape_combine_region(gdk,NULL,0,0);
        XSync(display,False);
        rects=XShapeGetRectangles(display,GDK_WINDOW_XID(gdk),ShapeInput,&count,&ordering);XFree(rects);
        if(count==0) { result=0;puts("X11 input shape: expanded receives clicks; hidden stays empty after stale native reset"); }
        gtk_main_quit();
    } else { fprintf(stderr,"Unexpected input region stage=%d count=%d\n",stage,count);gtk_main_quit(); }
}
static gboolean timeout(gpointer p){gtk_main_quit();return G_SOURCE_REMOVE;}
int main(int argc,char **argv){
    gtk_init(&argc,&argv);
    window=gtk_window_new(GTK_WINDOW_TOPLEVEL);
    WebKitWebView *view=WEBKIT_WEB_VIEW(webkit_web_view_new());
    gtk_container_add(GTK_CONTAINER(window),GTK_WIDGET(view));
    gtk_widget_realize(window); /* Realize, never show/map. */
    webkit_web_view_load_html(view,"<script>setTimeout(()=>document.title='Coucou Island | expanded | 640 | 160',100)</script>","tauri://localhost/");
    /* Loader connected the production shape handler first. */
    g_signal_connect(view,"notify::title",G_CALLBACK(title_changed),NULL);
    g_timeout_add_seconds(5,timeout,NULL);gtk_main();gtk_widget_destroy(window);return result;
}
