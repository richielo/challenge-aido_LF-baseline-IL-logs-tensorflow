#!/usr/bin/env python
import gym
from graph_utils import load_graph
import tensorflow as tf
from cnn_predictions import fun_img_preprocessing
# noinspection PyUnresolvedReferences
import gym_duckietown_agent  # DO NOT CHANGE THIS IMPORT (the environments are defined here)
from duckietown_challenges import wrap_solution, ChallengeSolution, ChallengeInterfaceSolution, InvalidSubmission

# Maximum forward robot speed in meters/second
ROBOT_SPEED = 0.30
# Distance (diameter) between the center of the robot wheels (10.2cm)
WHEEL_DIST = 0.102

def solve(gym_environment, cis):
    # python has dynamic typing, the line below can help IDEs with autocompletion
    assert isinstance(cis, ChallengeInterfaceSolution)
    # after this cis. will provide you with some autocompletion in some IDEs (e.g.: pycharm)
    cis.info('Creating model.')
    # you can have logging capabilities through the solution interface (cis).
    # the info you log can be retrieved from your submission files.

    # We get environment from the Evaluation Engine
    cis.info('Making environment')
    env = gym.make(gym_environment)
    # Then we make sure we have a connection with the environment and it is ready to go
    cis.info('Reset environment')
    observation = env.reset()
    # While there are no signal of completion (simulation done)
    # we run the predictions for a number of episodes, don't worry, we have the control on this part

    # Let's allow the user to pass the filename as an argument
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--frozen_model_filename", default="results/frozen_model.pb", type=str,
    #                     help="Frozen model file to import")
    frozen_model_filename = "frozen_graph.pb"
    # args = parser.parse_args()
    # We use our "load_graph" function
    graph = load_graph(frozen_model_filename)
    # We can verify that we can access the list of operations in the graph
    for op in graph.get_operations():
        print(op.name)
        # prefix/Placeholder/inputs_placeholder
        # ...
        # prefix/Accuracy/predictions

    # We access the input and output nodes
    x = graph.get_tensor_by_name('prefix/x:0')
    # x = tf.placeholder(tf.float16, shape=[None, 48 * 96], name='x')
    # y = tf.placeholder(tf.float16, shape=[None, 2], name='y')
    y = graph.get_tensor_by_name('prefix/ConvNet/fc_layer_2/BiasAdd:0')
    # We launch a Session
    with tf.Session(graph=graph) as sess:

        while True:
            # we passe the observation to our model, and we get an action in return

            # 48x96 is the image size the model expects
            # Additionally img is converted to greyscale
            observation = fun_img_preprocessing(observation, 48, 96)
            # this outputs omega, the desired angular velocity
            action = sess.run(y, feed_dict={
                x: observation
            })
            action = [action[0,1], action[0, 0]]
            # Inverse kinematics: Which left/right wheel velocities
            # correspond to the constant forward velocity and omega/angular velocity
            #
            # # adjusting k by gain and trim
            # # k_r_inv = (self.gain + self.trim) / k_r
            # # k_l_inv = (self.gain - self.trim) / k_l
            # omega_r = (ROBOT_SPEED + 0.5 * omega[0, 0] * WHEEL_DIST / 2.0)
            # omega_l = (ROBOT_SPEED - 0.5 * omega[0, 0] * WHEEL_DIST / 2.0)
            # action = [omega_l, omega_r]
            # TODO: remove printing
            # action = [ROBOT_SPEED, omega[0,0]]
            print(action)

            # we tell the environment to perform this action and we get some info back in OpenAI Gym style
            observation, reward, done, info = env.step(action)
            # here you may want to compute some stats, like how much reward are you getting
            # notice, this reward may no be associated with the challenge score.

            # it is important to check for this flag, the Evaluation Engine will let us know when should we finish
            # if we are not careful with this the Evaluation Engine will kill our container and we will get no score
            # from this submission
            if 'simulation_done' in info:
                break
            if done:
                env.reset()


class Submission(ChallengeSolution):
    def run(self, cis):
        assert isinstance(cis, ChallengeInterfaceSolution)  # this is a hack that would help with autocompletion

        # get the configuration parameters for this challenge
        params = cis.get_challenge_parameters()
        cis.info('Parameters: %s' % params)

        gym_environment = params['env']

        try:
            cis.info('Starting.')
            solve(gym_environment, cis)  # let's try to solve the challenge, exciting ah?
        except BaseException as e:
            raise InvalidSubmission(str(e))

        cis.set_solution_output_dict({})
        cis.info('Finished.')


if __name__ == '__main__':
    print('Starting submission')
    wrap_solution(Submission())