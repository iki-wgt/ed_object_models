function ed_object_models_setup {
        local model_path=`rospack find ed_object_models`/models
    
    if [ -z $GAZEBO_MODEL_PATH ]
    then
        export GAZEBO_MODEL_PATH=$model_path
    else
        export GAZEBO_MODEL_PATH=$model_path:$GAZEBO_MODEL_PATH
    fi

    export GAZEBO_MODEL_PATH="$(find $model_path -type f -name '*model.sdf' -printf '%h:')${GAZEBO_MODEL_PATH}"

}

ed_object_models_setup
