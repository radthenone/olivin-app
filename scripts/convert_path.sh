#!/usr/bin/env bash

convert_path() {
    local var_name="$1"
    local path="${!var_name}"

    if [[ "$path" == *":"* ]]; then
        path=$(cygpath "$path")
    fi

    export "$var_name"="$path"
}

convert_path ANDROID_HOME
