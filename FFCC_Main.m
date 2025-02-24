clear
close all
clc

load('lib_SwitchFilter_20_NoN.mat')
load('lib_libMfcc_20_NoN.mat')
load('lib_Lfcc_20_NoN.mat')
load('lib_IMfcc_20_NoN.mat')

load('false_SwitchFilter_20_NoN.mat')
load('false_libMfcc_20_NoN.mat')
load('false_Lfcc_20_NoN.mat')
load('false_IMfcc_20_NoN.mat')

commandAmount = 10;    % Command amount: 1 - 30

fprintf('lib_SwitchFilter:\n');
[SwitchFilterTPR,SwitchFilterFPR] = main(lib_SwitchFilter, false_SwitchFilter, commandAmount,2000);
fprintf('lib_libMfcc:\n');
[MfccTPR,MfccFPR] = main(lib_libMfcc, false_libMfcc, commandAmount,7500);
fprintf('lib_Lfcc:\n');
[LfccTPR,LfccFPR] = main(lib_Lfcc, false_Lfcc, commandAmount,3300);
fprintf('lib_IMfcc:\n');
[IMfccTPR,IMfccFPR] = main(lib_IMfcc, false_IMfcc, commandAmount,3000);
