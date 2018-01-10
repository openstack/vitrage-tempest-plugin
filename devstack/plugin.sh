# install_vitrage_tempest_plugin
function install_vitrage_tempest_plugin {
    setup_dev_lib "vitrage-tempest-plugin"
}

if [[ "$1" == "stack" ]]; then
    case "$2" in
        install)
            echo_summary "Installing vitrage-tempest-plugin"
            install_vitrage_tempest_plugin
            ;;
    esac
fi
