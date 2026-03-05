import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess, TimerAction, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    # Include the robot_state_publisher launch file, provided by our own package
    package_name = 'my_robot'  # <--- CHANGE ME

    # Robot State Publisher
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory(package_name), 'launch', 'rsp.launch.py')
        ]),
        launch_arguments={'use_sim_time': 'true'}.items()
    )


    default_world = os.path.join(
        get_package_share_directory(package_name),
        'worlds',
        'empty.world'
    )    
    world = LaunchConfiguration('world')

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=default_world,
        description='World to load'
    )

  
    # Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ]),
        launch_arguments={'gz_args': ['-r -v4 ', world], 'on_exit_shutdown': 'true'}.items()
    )

    # Spawn the robot
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description',
                   '-name', 'my_robot',
                   '-z', '0.1'],
        output='screen'
    )

    # # ROS-Gazebo bridge for cmd_vel, odom, joint_states, tf
    # bridge = ExecuteProcess(
    #     cmd=[
    #         'ros2', 'run', 'ros_gz_bridge', 'parameter_bridge',
    #         # '/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry',
    #         # '/joint_states@sensor_msgs/msg/JointState@gz.msgs.Model',
    #         # '/tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V',
    #         '/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
    #         # '/diff_cont/cmd_vel_unstamped@geometry_msgs/msg/Twist@gz.msgs.Twist',
    #         # '/clock@rosgraph_msgs/msg/Clock@gz.msgs.Clock',
    #     ],
    #     output='screen'
    # )
    
    # Controller spawners
    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont",  "--controller-manager", "/controller_manager"],
        output="screen",
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    # Delay controller spawning until robot + Gazebo are ready
    spawn_controllers = TimerAction(
        period=5.0,
        actions=[joint_broad_spawner, diff_drive_spawner]
    )
    bridge_params = os.path.join(get_package_share_directory(package_name),'config','gz_bridge.yaml')
    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={bridge_params}',
        ]
    )

    # Relay: /cmd_vel (Twist) -> /diff_cont/cmd_vel (TwistStamped)
    twist_to_stamped = Node(
        package='my_robot',
        executable='twist_to_stamped.py',   # because we installed via CMake PROGRAMS
        name='twist_to_stamped',
        output='screen'
    )

    #     # PS5 Controller input
    # Node(
    #     package='joy',
    #     executable='joy_node',
    #     name='joy_node',
    #     output='screen',
    #     parameters=[{
    #         "dev": "/dev/input/js0",    # Joystick device
    #         "deadzone": 0.05,
    #         "autorepeat_rate": 20.0
    #     }]
    # ),

    # # Convert joystick input to /cmd_vel
    # Node(
    #     package='teleop_twist_joy',
    #     executable='teleop_node',
    #     name='teleop_twist_joy',
    #     output='screen',
    #     parameters=["config/ps5_teleop.yaml"]
    # )

  
    # Optional: RViz
    # rviz = ExecuteProcess(
    #     cmd=['rviz2'],
    #     output='screen'
    # )

    # Launch everything
    return LaunchDescription([
        rsp,
        world_arg,
        gazebo,
        spawn_entity,
        spawn_controllers,
        # clock_bridge,
        # bridge,
        ros_gz_bridge,
        twist_to_stamped,
    ])
