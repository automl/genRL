#!/usr/bin/env bash

python run_context_gating.py '+experiment=glob(*)' '+algorithm=sac' 'contexts.context_feature_args=[],[g],[max_speed],[l],[m],[dt]' 'carl.state_context_features=null,${contexts.context_feature_args}'  'seed=range(0,5)' 'carl.gaussian_noise_std_percentage=0.4' --multirun