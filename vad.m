
function [activeNum, pos] = vad_YW(speech, fs, plotMode, activeBuffer, activeMax, energyTh2)
%%     By YI-WEN CHEN, 2017
%     1. Voice activity detection by spectral energy.
%     2. Read more at www.jarvus.net
% 
%     Required Input Parameters : 
%       speech      Speech data
%       fs          Sampling frequency (Hz)
% 
%     Optional Input Parameters : 
%       pllotMode   0: don't plot anything
%                   1: plot VAD result in time domain signal
%                   2: plot all of segments of active parts respectively
%                   3: plot all of above mentioned
%       activeBuffer  Buffer range in two sides (sec)
%       activeMax     Max active length (sec)
%       energyTh2     Under spectral energy for removal
%
%     Output Parameters : 
%       activeNum   The amount of active speech segment
%       pos         Active segments samples position
%
%     Example : 
%       [ speech, fs] = audioread( 'Music_SNR_5_0.wav' );
%       [ activeNum, pos] = vad_YW(speech, fs, 3);
[ speech2, fs ] = audioread( 'Clean_5.wav' );
%% ------- paramters  --------
if ( nargin < 3)
    plotMode = 0;
end
if ( nargin < 4)
    activeBuffer = 0.5; % buffer range in two sides (sec)
end
if ( nargin < 5)
    activeMax = 3;      % max active length (sec)
end
if ( nargin < 6)
    energyTh2 = 0;      % under spectral energy for removal
end
frameT = 32;        % window length is 32 ms
shiftP = 1/2;       % Shift percentage is 50%

minFreq = 1000;      % extract min frequency
maxFreq = 4000;     % extract max frequency

noiseTh = 3;        % under 3 frames shoube be removed
speechTh = 15;      % max 15 silence frames between two active side should be active 
energyTh = 0;       % under spectral energy for removal

%% --------- main algorithm ---------------

ns_length = length(speech);
sampleTime = ( 1:ns_length )/fs;
frameSize = fix(frameT*0.001*fs);   % window length is 32 ms
NFFT = 2*frameSize;                 % FFT size is twice the window length
hanWin = hanning(frameSize);
overlap = fix((1-shiftP)*frameSize);   % overlap between sucessive frames
offset = frameSize - overlap;

% iteration times
max_m = fix((ns_length - NFFT)/offset);
frameTime = ((0:max_m)*(frameSize-overlap)+0.5*frameSize)/fs;

perFreq = (fs/2)/frameSize;
removeFreqMask = zeros(NFFT, 1);
removeFreqMask(floor(minFreq/perFreq):floor(maxFreq/perFreq)) = 1;
removeFreqMask(NFFT-floor(maxFreq/perFreq)+1:NFFT-floor(minFreq/perFreq)+1) = 1;

energy = zeros(max_m+1,1);
energyNew = zeros(max_m+1,1);
% ns_new1 = zeros(ns_length,1);

%Iteration
%% --------------- VAD ---------------------
for m = 0 : max_m
    begin = m*offset + 1;    
    finish = m*offset + frameSize;   
    s = speech(begin:finish);       %extract speech segment
    winY = hanWin.*s;               %perform hanning window
    fftY = fft(winY, NFFT);         %perform fast fourier transform
%     phaseY = phase(fftY);                %extract magnitude
    magY = abs(fftY);                %extract magnitude
   
%    negative spectrum removal
	magY = 20*log10(magY);
%    apply frequency mask
    magY = magY.*removeFreqMask;
   
   for i = 1:NFFT/2
       if ( magY(i) < -energyTh )
           magY(i) = 0;
       else
           magY(i) = magY(i) + energyTh;
       end
   end
   energy(m+1) = sum(magY(1:NFFT/2));
%    fftY = magY.*exp(i*phaseY);        
%    ns_new1(begin:begin + NFFT-1) = ns_new1(begin:begin + NFFT-1) + real(ifft(fftY,NFFT));
end


%% --------------- Filter ---------------------
plot(energy);
speech_max = max(speech);
noCont = 0;
isCont = 0;

for i = 1:max_m
   if ( energy(i) > energyTh2 )
       energy(i) = speech_max;
       noCont = 0;
       isCont = isCont + 1;
       if i+speechTh > max_m+1
           tempEnd = max_m+1;
       else
           tempEnd = i+speechTh;
       end
       if ( isCont <= noiseTh && sum(energy(i+1:tempEnd) == 0) == speechTh)
           if ( i-isCont < 1 )
               tempBegin = 1;
           else
               tempBegin = i-isCont;
           end
           energy(tempBegin:i) = 0;
       end
   else
       energy(i) = 0;
       isCont = 0;
       noCont = noCont + 1;
       if ( noCont <= speechTh && energy(i+1) > 0 && i > speechTh )
           if ( i-noCont < 1 )
               tempBegin = 1;
           else
               tempBegin = i-noCont;
           end
           energy(tempBegin:i) = speech_max;
       end
   end
end
if ( energy(max_m+1) > energyTh2)
    energy(max_m+1) = speech_max;
else
    energy(max_m+1) = 0;
end
% figure;
% plot(energy);

%% --------------- Extract segment ---------------------
[frameMin, frameIdx] = min(abs(frameTime - activeBuffer));
activeNum = 0;
temp = 1;
% len, active, pos
pos = zeros(1,2);

for i = 1:max_m
    if ( energy(i) == 0 && energy(i+1) > 0 )
        temp = i;
    end
    if ( energy(i) > 0 && energy(i+1) == 0 )
        if ( ( frameTime(i)-frameTime(temp)) <  activeMax)
            activeNum = activeNum + 1;
            pos(activeNum,1) = temp;
            pos(activeNum,2) = i;
        else
            energy(temp:i) = 0;
        end
        
    end
end
pos(:,1) = pos(:,1) - frameIdx;
pos(:,2) = pos(:,2) + frameIdx;
for i = 1:activeNum
    if ( pos(i,1) < 1 )
        pos(i,1) = 1;
    end
    if ( pos(i,2) > max_m+1)
        pos(i,2) = max_m;
    end
    energyNew(pos(i,1):pos(i,2)) = speech_max;
end
% transfer pos [frame] to [sample]
pos(:,1) = pos(:,1)*offset + 1;
pos(:,2) = pos(:,2)*offset + frameSize;
    
%% --------------- Output ---------------------
if ( plotMode == 1 || plotMode == 3 )
    figure;
    subplot(2,1,1);
    hold on;
    plot(sampleTime, speech); 
    plot(frameTime, energy,'r','linewidth',2);
    title('VAD');
    xlabel('Time (s)'); ylabel('Amp');
    subplot(2,1,2);
    hold on;
    plot(sampleTime, speech2); 
%     plot(frameTime, energyNew,'r','linewidth',2);
%     title(['VAD with buffer range(s): ', num2str(activeBuffer)]);
%     xlabel('Time (s)'); ylabel('Amp');
end
if ( plotMode == 2 || plotMode == 3 )
    for i = 1:activeNum
        figure;
        plot(sampleTime(pos(i,1):pos(i,2)), speech(pos(i,1):pos(i,2))); 
%         wavwrite(speech(pos(i,1):pos(i,2)),fs,16,[num2str(i) '.wav']);
        title(['after VAD signal: ', num2str(i)]);
        xlabel('Time (s)'); ylabel('Amp');
    end
end




import numpy as np

# 假設以下變數已經初始化
# speech, energy, energyTh2, speechTh, noiseTh, max_m, frameTime, activeBuffer, activeMax

speech_max = np.max(speech)
noCont = 0
isCont = 0

# 能量處理
for i in range(max_m):
    if energy[i] > energyTh2:
        energy[i] = speech_max
        noCont = 0
        isCont += 1
        
        tempEnd = min(i + speechTh, max_m)
        
        if isCont <= noiseTh and np.sum(energy[i+1:tempEnd] == 0) == speechTh:
            tempBegin = max(i - isCont, 0)
            energy[tempBegin:i+1] = 0
    else:
        energy[i] = 0
        isCont = 0
        noCont += 1
        
        if noCont <= speechTh and i > speechTh and energy[i+1] > 0:
            tempBegin = max(i - noCont, 0)
            energy[tempBegin:i+1] = speech_max

# 處理最後一帧
if energy[max_m] > energyTh2:
    energy[max_m] = speech_max
else:
    energy[max_m] = 0

# 提取語音片段
frameMin = np.min(np.abs(frameTime - activeBuffer))
frameIdx = np.argmin(np.abs(frameTime - activeBuffer))
activeNum = 0
pos = []

for i in range(max_m):
    if energy[i] == 0 and energy[i+1] > 0:
        temp = i
    if energy[i] > 0 and energy[i+1] == 0:
        if (frameTime[i] - frameTime[temp]) < activeMax:
            activeNum += 1
            pos.append((temp, i))
        else:
            energy[temp:i+1] = 0

# pos 將包含每個檢測到的語音片段的位置

