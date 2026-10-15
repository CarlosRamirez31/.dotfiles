local awful = require("awful")

return function()
    awful.spawn.with_shell([[
        choice=$(printf 'Bloquear\nCerrar sesión\nReiniciar…\nApagar…\n' | rofi -dmenu -i -p 'Sesión') || exit 0
        case $choice in
            'Bloquear') exec "$HOME/.local/bin/dotfiles-lock" ;;
            'Cerrar sesión') exec awesome-client 'awesome.quit()' ;;
            'Reiniciar…')
                answer=$(printf 'Cancelar\nConfirmar reinicio\n' | rofi -dmenu -i -p '¿Reiniciar?') || exit 0
                [ "$answer" = 'Confirmar reinicio' ] && exec systemctl reboot
                ;;
            'Apagar…')
                answer=$(printf 'Cancelar\nConfirmar apagado\n' | rofi -dmenu -i -p '¿Apagar?') || exit 0
                [ "$answer" = 'Confirmar apagado' ] && exec systemctl poweroff
                ;;
        esac
    ]])
end
