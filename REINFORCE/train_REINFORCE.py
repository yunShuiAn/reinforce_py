import os
import argparse
import gym
import numpy as np
import tensorflow as tf

from agent import REINFORCE
from utils import *

def main(args):
    MODEL_PATH = args.model_path
    INPUT_DIM = 80 * 80
    HIDDEN_UNITS = 200
    ACTION_DIM = 6
    MAX_EPISODES = 20000
    MAX_STEPS = 5000

    # load agent
    agent = REINFORCE(INPUT_DIM, HIDDEN_UNITS, ACTION_DIM)
    agent.construct_model(args.gpu)

    # model saver
    saver = tf.train.Saver(max_to_keep=1)
    if MODEL_PATH is not None:
        saver.restore(agent.sess, args.model_path)
        ep_base = int(args.model_path.split('_')[-1])
        mean_rewards = float(args.model_path.split('/')[-1].split('_')[0])
    else:
        agent.sess.run(tf.global_variables_initializer())
        ep_base = 0
        mean_rewards = None

    # load env
    env = gym.make("Pong-v0")
    # main loop
    for ep in xrange(MAX_EPISODES):
        # reset env
        total_rewards = 0
        state = env.reset()

        for step in xrange(MAX_STEPS):
            # preprocess
            state = preprocess(state)
            # sample actions
            action = agent.sample_action(state[np.newaxis,:])
            # act!
            next_state, reward, done, _ = env.step(action)

            total_rewards += reward
            agent.store_rollout(state, action, reward)
            # state shift
            state = next_state

            if done:
                break

        # update model per episode
        agent.update_model()

        # logging
        if mean_rewards is None:
            mean_rewards = total_rewards
        else:
            mean_rewards = 0.99 * mean_rewards + 0.01 * total_rewards
        rounds = (21 - np.abs(total_rewards)) + 21
        average_steps = (step + 1) / rounds
        print 'Ep%s: %d rounds \nAverage_steps: %.2f Reward: %s Average_reward: %.4f' % \
                                    (ep+1, rounds, average_steps, total_rewards, mean_rewards)
        if ep % 100 == 0:
            if not os.path.isdir(args.save_path):
                os.makedirs(args.save_path)
            saver.save(agent.sess,
                args.save_path + str(round(mean_rewards,2))+'_'+str(ep_base+ep+1))

def args_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', default=None,
            help='Whether to use a saved model. (*None|model path)')
    parser.add_argument('--save_path', default='./model/',
            help='Path to save a model during training.')
    parser.add_argument('--gpu', default=-1,
            help='running on a specify gpu, -1 indicates using cpu')
    return parser.parse_args()

if __name__ == '__main__':
    main(args_parse())
