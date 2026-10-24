/* Apply a local WebKit user stylesheet only to Coucou. No app files are patched. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <string.h>
#include <stdio.h>
#include <gio/gunixsocketaddress.h>
#include <glib/gstdio.h>
#include <sys/stat.h>
#include <unistd.h>
#include <webkit2/webkit2.h>

/* Same-user, local-only container transport; lives and stops with Coucou. */
static gboolean hermes_event(GThreadedSocketService *service, GSocketConnection *incoming,
        GObject *object, gpointer data) {
    gchar message[16384]; gsize used = 0; GError *error = NULL;
    g_socket_set_timeout(g_socket_connection_get_socket(incoming), 1);
    GInputStream *input = g_io_stream_get_input_stream(G_IO_STREAM(incoming));
    while (used < sizeof(message)) {
        gssize n = g_input_stream_read(input, message + used, sizeof(message) - used, NULL, &error);
        if (n <= 0) break;
        used += n;
        if (memchr(message, '\n', used)) break;
    }
    g_clear_error(&error);
    if (used && used < sizeof(message) && memchr(message, '\n', used)) {
        gchar *path = g_build_filename(g_get_user_runtime_dir(), "coucou.sock", NULL);
        GSocketClient *client = g_socket_client_new();
        g_socket_client_set_timeout(client, 1);
        GSocketAddress *address = g_unix_socket_address_new(path);
        GSocketConnection *native = g_socket_client_connect(client, G_SOCKET_CONNECTABLE(address), NULL, &error);
        if (native) {
            g_output_stream_write_all(g_io_stream_get_output_stream(G_IO_STREAM(native)),
                message, used, NULL, NULL, &error);
            g_clear_error(&error);
            gchar ack;
            /* Native non-approval events finish only after emission: preserve event order. */
            g_input_stream_read(g_io_stream_get_input_stream(G_IO_STREAM(native)), &ack, 1, NULL, &error);
            g_clear_error(&error);
            g_io_stream_close(G_IO_STREAM(native), NULL, NULL); g_object_unref(native);
        }
        g_clear_error(&error); g_object_unref(address); g_object_unref(client); g_free(path);
    }
    g_io_stream_close(G_IO_STREAM(incoming), NULL, NULL);
    return TRUE;
}

static void start_hermes_transport(void) {
    static GSocketService *service = NULL;
    if (service || g_strcmp0(g_getenv("COUCOU_HERMES_BRIDGE"), "1") != 0) return;
    gchar *directory = g_build_filename(g_get_home_dir(), ".local", "share", "coucou", "hermes-bridge", NULL);
    g_mkdir_with_parents(directory, 0700); g_chmod(directory, 0700);
    gchar *path = g_build_filename(directory, "event.sock", NULL);
    struct stat previous;
    if (lstat(path, &previous) == 0) {
        if (!S_ISSOCK(previous.st_mode) || previous.st_uid != getuid()) {
            g_free(path); g_free(directory); return;
        }
        g_unlink(path);
    }
    GError *error = NULL;
    GSocketAddress *address = g_unix_socket_address_new(path);
    service = g_threaded_socket_service_new(1);
    if (!g_socket_listener_add_address(G_SOCKET_LISTENER(service), address, G_SOCKET_TYPE_STREAM,
            G_SOCKET_PROTOCOL_DEFAULT, NULL, NULL, &error)) {
        g_warning("Coucou Hermes bridge: %s", error->message); g_clear_error(&error);
        g_clear_object(&service);
    } else {
        g_chmod(path, 0600);
        g_signal_connect(service, "run", G_CALLBACK(hermes_event), NULL);
        g_socket_service_start(service);
    }
    g_object_unref(address); g_free(path); g_free(directory);
}

typedef struct {
    WebKitScriptMessageReply *reply;
    JSCContext *context;
} HubReply;

static void hub_completed(GObject *source, GAsyncResult *result, gpointer data) {
    HubReply *pending = data;
    gchar *out = NULL, *err = NULL;
    GError *error = NULL;
    if (!g_subprocess_communicate_utf8_finish(G_SUBPROCESS(source), result, &out, &err, &error)) {
        webkit_script_message_reply_return_error_message(pending->reply, error->message);
        g_clear_error(&error);
    } else {
        JSCValue *value = out ? jsc_value_new_from_json(pending->context, out) : NULL;
        if (value && jsc_value_is_object(value))
            webkit_script_message_reply_return_value(pending->reply, value);
        else
            webkit_script_message_reply_return_error_message(pending->reply,
                err && *err ? err : "Coucou Agent Hub: respuesta no válida");
        if (value) g_object_unref(value);
    }
    g_free(out); g_free(err);
    webkit_script_message_reply_unref(pending->reply);
    g_object_unref(pending->context);
    g_free(pending);
}

static gboolean open_session(WebKitUserContentManager *manager, JSCValue *message,
        WebKitScriptMessageReply *reply, gpointer data) {
    gchar *json = jsc_value_to_json(message, 0);
    if (!json || strlen(json) > 1024 * 1024) {
        webkit_script_message_reply_return_error_message(reply, "Solicitud de terminal no válida");
        g_free(json); return TRUE;
    }
    gchar *backend = g_build_filename(g_get_home_dir(), ".local", "opt", "coucou",
        "agent-hub", "agent_hub_terminal.py", NULL);
    const char *test_backend = g_getenv("COUCOU_AGENT_HUB_TEST_BACKEND");
    const gchar *argv[] = { "/usr/bin/python3", test_backend ? test_backend : backend, NULL };
    gchar **environment = g_get_environ();
    environment = g_environ_unsetenv(environment, "LD_PRELOAD");
    environment = g_environ_unsetenv(environment, "LD_LIBRARY_PATH");
    environment = g_environ_unsetenv(environment, "COUCOU_POLYBAR_CSS");
    GSubprocessLauncher *launcher = g_subprocess_launcher_new(
        G_SUBPROCESS_FLAGS_STDIN_PIPE | G_SUBPROCESS_FLAGS_STDOUT_PIPE | G_SUBPROCESS_FLAGS_STDERR_PIPE);
    g_subprocess_launcher_set_environ(launcher, environment);
    GError *error = NULL;
    GSubprocess *process = g_subprocess_launcher_spawnv(launcher, argv, &error);
    if (!process) {
        webkit_script_message_reply_return_error_message(reply, error->message);
        g_clear_error(&error);
    } else {
        HubReply *pending = g_new0(HubReply, 1);
        pending->reply = webkit_script_message_reply_ref(reply);
        pending->context = g_object_ref(jsc_value_get_context(message));
        g_subprocess_communicate_utf8_async(process, json, NULL, hub_completed, pending);
        g_object_unref(process);
    }
    g_object_unref(launcher);
    g_strfreev(environment); g_free(backend); g_free(json);
    return TRUE;
}

/* A visually hidden island must have an empty X11 input shape, even if the
 * native collapsed wake strip or a late resize tries to restore its rectangle.
 * Polybar hover is handled independently by Awesome; WebKit remains mapped. */
void gdk_window_input_shape_combine_region(GdkWindow *window, const cairo_region_t *region, gint x, gint y) {
    static void (*original)(GdkWindow *, const cairo_region_t *, gint, gint);
    if (!original) original = dlsym(RTLD_NEXT, "gdk_window_input_shape_combine_region");
    if (g_object_get_data(G_OBJECT(window), "coucou-pass-through")) {
        cairo_region_t *empty = cairo_region_create();
        original(window, empty, 0, 0); cairo_region_destroy(empty);
    } else original(window, region, x, y);
}

static void publish_geometry(WebKitWebView *view, GParamSpec *pspec, gpointer data) {
    const gchar *title = webkit_web_view_get_title(view);
    if (!title || !g_str_has_prefix(title, "Coucou Island | ")) return;
    GtkWidget *top = gtk_widget_get_toplevel(GTK_WIDGET(view));
    if (GTK_IS_WINDOW(top)) {
        gtk_window_set_title(GTK_WINDOW(top), title);
        GdkWindow *window = gtk_widget_get_window(top);
        if (!window) return;
        gboolean hidden = !g_str_has_prefix(title, "Coucou Island | expanded |");
        g_object_set_data(G_OBJECT(window), "coucou-pass-through", GINT_TO_POINTER(hidden));
        int width = 0, height = 0, outer_width = 0, outer_height = 0;
        if (!hidden && sscanf(title, "Coucou Island | expanded | %d | %d", &width, &height) == 2) {
            gtk_window_get_size(GTK_WINDOW(top), &outer_width, &outer_height);
            cairo_rectangle_int_t rectangle = { MAX(0, (outer_width-width)/2), 0, width, height };
            cairo_region_t *region = cairo_region_create_rectangle(&rectangle);
            gdk_window_input_shape_combine_region(window, region, 0, 0);
            cairo_region_destroy(region);
        } else {
            cairo_region_t *empty = cairo_region_create();
            gdk_window_input_shape_combine_region(window, empty, 0, 0);
            cairo_region_destroy(empty);
        }
    }
}
static void apply_theme(WebKitWebView *view) {
    start_hermes_transport();
    if (!g_object_get_data(G_OBJECT(view), "coucou-polybar-theme")) {
        g_object_set_data(G_OBJECT(view), "coucou-polybar-theme", GINT_TO_POINTER(1));
        g_signal_connect(view, "notify::title", G_CALLBACK(publish_geometry), NULL);
        WebKitUserContentManager *manager = webkit_web_view_get_user_content_manager(view);
        webkit_user_content_manager_register_script_message_handler_with_reply(manager,
            "coucouAgentHub", NULL);
        g_signal_connect(manager, "script-message-with-reply-received::coucouAgentHub",
            G_CALLBACK(open_session), NULL);
        gchar *css = NULL;
        const char *path = g_getenv("COUCOU_POLYBAR_CSS");
        if (path && g_file_get_contents(path, &css, NULL, NULL)) {
            WebKitUserStyleSheet *sheet = webkit_user_style_sheet_new(css,
                WEBKIT_USER_CONTENT_INJECT_TOP_FRAME, WEBKIT_USER_STYLE_LEVEL_USER, NULL, NULL);
            webkit_user_content_manager_add_style_sheet(manager, sheet);
            webkit_user_style_sheet_unref(sheet);
            g_free(css);
        }
        if (path) {
            gchar *directory = g_path_get_dirname(path);
            gchar *bridge_path = g_build_filename(directory, "open-session.js", NULL);
            gchar *bridge = NULL;
            if (g_file_get_contents(bridge_path, &bridge, NULL, NULL)) {
                WebKitUserScript *script = webkit_user_script_new(bridge,
                    WEBKIT_USER_CONTENT_INJECT_TOP_FRAME, WEBKIT_USER_SCRIPT_INJECT_AT_DOCUMENT_END,
                    NULL, NULL);
                webkit_user_content_manager_add_script(manager, script);
                webkit_user_script_unref(script);
                g_free(bridge);
            }
            g_free(bridge_path);
            g_free(directory);
        }
        /* Expose only panel geometry to the window manager for hover dismissal. */
        const char *js = "setInterval(()=>{const e=document.getElementById('island');if(!e)return;"
            "const r=(document.querySelector('dialog[open]')||e).getBoundingClientRect();const mode=r.height<8?'hidden':r.height<90?'compact':'expanded';"
            "e.style.opacity=mode==='expanded'?'1':'0';const title='Coucou Island | '+mode+' | '+Math.round(r.width)+' | '+Math.round(r.height);"
            "if(document.title!==title)document.title=title;},150);";
        WebKitUserScript *script = webkit_user_script_new(js, WEBKIT_USER_CONTENT_INJECT_TOP_FRAME,
            WEBKIT_USER_SCRIPT_INJECT_AT_DOCUMENT_END, NULL, NULL);
        webkit_user_content_manager_add_script(manager, script);
        webkit_user_script_unref(script);
    }
}
void webkit_web_view_load_uri(WebKitWebView *view, const gchar *uri) {
    static void (*original)(WebKitWebView *, const gchar *);
    if (!original) original = dlsym(RTLD_NEXT, "webkit_web_view_load_uri");
    apply_theme(view); original(view, uri);
}
void webkit_web_view_load_request(WebKitWebView *view, WebKitURIRequest *request) {
    static void (*original)(WebKitWebView *, WebKitURIRequest *);
    if (!original) original = dlsym(RTLD_NEXT, "webkit_web_view_load_request");
    apply_theme(view); original(view, request);
}
void webkit_web_view_load_html(WebKitWebView *view, const gchar *html, const gchar *base) {
    static void (*original)(WebKitWebView *, const gchar *, const gchar *);
    if (!original) original = dlsym(RTLD_NEXT, "webkit_web_view_load_html");
    apply_theme(view); original(view, html, base);
}

void webkit_user_content_manager_add_script(WebKitUserContentManager *manager, WebKitUserScript *script) {
    static void (*original)(WebKitUserContentManager *, WebKitUserScript *);
    if (!original) original = dlsym(RTLD_NEXT, "webkit_user_content_manager_add_script");
    if (!g_object_get_data(G_OBJECT(manager), "coucou-invoke-bootstrap")) {
        g_object_set_data(G_OBJECT(manager), "coucou-invoke-bootstrap", GINT_TO_POINTER(1));
        const char *js = "(()=>{const define=Object.defineProperty;Object.defineProperty=function(target,key,desc){"
            "if(target===window.__TAURI_INTERNALS__&&key==='invoke'&&typeof desc.value==='function'){"
            "const native=desc.value;window.__coucouNativeInvoke=native;Object.defineProperty=define;"
            "return define(target,key,{...desc,value:function(cmd,args,options){"
            "if(window.__coucouAgentHubInvoke)return window.__coucouAgentHubInvoke(cmd,args,options);"
            "if(cmd==='open_session')return Promise.reject(new Error('El puente de Agent Hub aún no está disponible'));"
            "return native.call(this,cmd,args,options)}})}return define(target,key,desc)}})();";
        WebKitUserScript *bootstrap = webkit_user_script_new(js, WEBKIT_USER_CONTENT_INJECT_TOP_FRAME,
            WEBKIT_USER_SCRIPT_INJECT_AT_DOCUMENT_START, NULL, NULL);
        original(manager, bootstrap); webkit_user_script_unref(bootstrap);
    }
    original(manager, script);
}
