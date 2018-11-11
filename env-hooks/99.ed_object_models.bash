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

    model_paths_string="$(find $model_path -type f -name '*model.sdf' -printf '%h:')"
    if [ -z $model_paths_string ]
    then
        export GAZEBO_MODEL_PATH="${model_paths_string}${GAZEBO_MODEL_PATH}"
        export GAZEBO_RESOURCE_PATH="${model_paths_string}${GAZEBO_RESOURCE_PATH}"
    fi

}

ed_object_models_setup
