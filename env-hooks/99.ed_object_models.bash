function ed_object_models_setup {
        local model_path=`rospack find ed_object_models`/models
    
    if [ -z $GAZEBO_MODEL_PATH ]
    then
        export GAZEBO_MODEL_PATH=$model_path
    else
        export GAZEBO_MODEL_PATH=$model_path:$GAZEBO_MODEL_PATH
    fi
    if [ -z $GAZEBO_RESOURCE_PATH ]
    then
        export GAZEBO_RESOURCE_PATH=$model_path
    else
        export GAZEBO_RESOURCE_PATH=$model_path:$GAZEBO_RESOURCE_PATH
    fi

    local model_paths=($(find $model_path -type f -name '*model.sdf' | xargs dirname | xargs dirname))
    local unique_model_paths=$(printf "%s\n" "${model_paths[@]}" | sort -u | tr '\n' ' ')
    local model_paths_string=""
    for dir in $unique_model_paths
    do
        if [[ "$dir" == "$model_path" ]]
        then
            continue
        fi
        model_paths_string="$dir:$model_paths_string"
    done
    if [ -n $model_paths_string ]
    then
        export GAZEBO_MODEL_PATH="${model_paths_string}${GAZEBO_MODEL_PATH}"
        export GAZEBO_RESOURCE_PATH="${model_paths_string}${GAZEBO_RESOURCE_PATH}"
    fi

}

ed_object_models_setup
