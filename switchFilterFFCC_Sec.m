function [coeff] = switchFilterFFCC_Sec( speech, fs, FormantTh ,delta)
    
    if nargin < 4 
        delta = 0;
    end
    %% --------- parameters ---------------
    alpha = 0.97;               % pre-emphasis coefficient
    coefficients = 13;          % number 0of cepstral coefficients  13
    L = 30;             % cepstral sine lifter parameter  22.
    filterbank = 80;    % number of filterbank channels
    frameT = 32;        % window length is 32 ms
    shiftP = 1/2;       % Shift percentage is 50

    %% --------- main algorithm ---------------
    s_length = length(speech);
    frameSize = fix(frameT*0.001*fs);       % window length is 32 ms
    NFFT = 2*frameSize;                     % FFT size is twice the window length
    hanWin = hanning(frameSize);
    overlap = fix((shiftP)*frameSize);    % overlap between sucessive frames
    offset = frameSize - overlap;
    max_m = fix((s_length - frameSize)/offset);  % iteration times

    magNew = zeros(frameSize,max_m+1);
    MFcoeff = zeros(coefficients,max_m+1);
    speech = filter( [1 -alpha], 1, speech ); 
    hz2mel = @( hz )( 1125*log(1+hz/700) );     % Hertz to mel warping function
    mel2hz = @( mel )( 700*exp(mel/1125)-700 ); % mel to Hertz warping function
    
    dctm = @( N, M )( sqrt(2.0/M) * cos( repmat([0:N-1].',1,M).* repmat(pi*([1:M]-0.5)/M,N,1) ) );  % (eq 5.14)
    DCT = dctm(coefficients, filterbank);
    ceplifter = @( N, L )( 1+0.5*L*sin(pi*[0:N-1]/L) ); % Cepstral lifter routine (eq 5.16)
    lifter = ceplifter( coefficients, L );
    sigma = 2500;
    Formant = [];
    for m = 0 : max_m
        begin = m*offset + 1;    
        finish = m*offset + frameSize;   
        s = speech(begin:finish).*hanWin;
        % FFT
        mag = abs( fft(s, NFFT) ); 
        if ( sum(mag) ~= 0 )
            magNew(:,m+1) = mag(1:frameSize,:).*mag(1:frameSize,:);
        else
            magNew(:,m+1) = eps;
        end
        
        [Lpc_Formant] = energyExtract(s, fs, FormantTh);
        Formant = [Formant; Lpc_Formant];
        if (isempty(Lpc_Formant))
            a = 100;
            GMMfreqRange = [1 8000];
            GtoHz = @( mel )(exp(-((mel-a).^2)/(2*sigma.^2)));
            [triF3, freq] = GMMtrifbank( filterbank, frameSize, GMMfreqRange, fs, GtoHz);
        else
            [maxFormant] = round(Lpc_Formant(1)/100);
            a = maxFormant*100;
            GMMfreqRange = [1 8000];   
            GtoHz = @( mel )(exp(-((mel-a).^2)/(2*sigma.^2)));
            [triF3, freq] = GMMtrifbank( filterbank, frameSize, GMMfreqRange, fs, GtoHz);
        end
%         plot(freq,triF3);
        magNewMF(:,m+1) = triF3 * magNew(:,m+1);
    end
%     figure;imagesc(log(magNewMF));
%     coeff = abs(magNewMF.^(1/3));
    coeff = log(magNewMF);
%     magDCT = DCT*log(magNewMF);
%     coeff = diag( lifter )*magDCT;
    
%     if ( delta > 0 )
%         coeff2(:,2:size(coeff,2)+1) = coeff;
%         coeff2(:,1) = coeff2(:,2);
%         coeff2(:,size(coeff2,2)+1) = coeff2(:,size(coeff2,2));
%         for i = 2:size(coeff,2)+1
%             if ( delta >= 1 )
%                 coeff(14:26,i-1) = -0.5*coeff2(:,i-1) + 0.5*coeff2(:,i+1);
%             end
%             if ( delta == 2 )
%                 coeff(27:39,i-1) = coeff2(:,i-1) -2*coeff2(:,i) + coeff2(:,i+1);
%             end
%         end
%         coeff = coeff(1:end,:);
%     end
function [ H, f, c ] = GMMtrifbank( M, K, R, fs, h2w)

    f_min = 0;          % filter coefficients start at this frequency (Hz)
    f_low = R(1);       % lower cutoff frequency (Hz) for the filterbank 
    f_high = R(2);      % upper cutoff frequency (Hz) for the filterbank 
    f_max = 0.5*fs;     % filter coefficients end at this frequency (Hz)
    f = linspace( f_min, f_max, K ); % frequency range (Hz), size 1xK

    c = f_low+[0:M+1]*((f_high-f_low)/(M+1));
    c2 = h2w(f_low+[0:M+1]*((f_high-f_low)/(M+1)));
    c2((c2>1))=1;
    H = zeros( M, K );                  % zero otherwise
    
    for m = 1:M 
        % Without normalize
        k = f>=c(m)&f<=c(m+1); % up-slope
        H(m,k) = 2*(f(k)-c(m)) / ((c(m+2)-c(m))*(c(m+1)-c(m)));
        k = f>=c(m+1)&f<=c(m+2); % down-slope
        H(m,k) = 2*(c(m+2)-f(k)) / ((c(m+2)-c(m))*(c(m+2)-c(m+1)));
        
        %     % Without normalize
%         k = f>=c2(m)&f<=c2(m+1); % up-slope
%         H(m,k) = 2*(f(k)-c2(m)) / ((c2(m+2)-c2(m))*(c2(m+1)-c2(m)));
%         k = f>=c2(m+1)&f<=c2(m+2); % down-slope
%         H(m,k) = 2*(c2(m+2)-f(k)) / ((c2(m+2)-c2(m))*(c2(m+2)-c2(m+1)));
    end
        
H = H./repmat(max(H,[],2),1,K);  % normalize to unit height (inherently done)

for m = 1:M 
     H(m,:) = H(m,:)*c2(m+1);
end