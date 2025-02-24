function [Lpc_Formant,n_lpc_freq,FFT_test] = energyExtract(signal, fs, TH)


if ( nargin < 3)
     TH = 0.3;
end
%%-------------把计砞﹚----------
lpc_Order=20;
% Coefficient玒计
a_Coefficient=lpc(signal,lpc_Order);
est_x = filter([0 -a_Coefficient(2:end)],1,signal); %︳璸獺腹
e = signal - est_x;%箇璸岿粇
G=sqrt(mean(e.^2)); %糤痲 G
f_max=floor(length(signal)/2);
ns_length = length(signal);
H_f=zeros(f_max,1);

LPC_Peak=zeros(f_max,1);
n_lpc_freq=(0:(f_max-1))/f_max*fs/2;%﹚竡x禸繵瞯
sampleTime = ( 1:ns_length )/fs;

A = zeros(f_max,1,1);
for indexf=0:(f_max-1)
    H_f_sum=0;
    for index_k=1:lpc_Order
       H_f_sum=H_f_sum+a_Coefficient(1,1+index_k)*exp((-1i*pi*index_k*indexf)/f_max);
    end
    H_f(indexf+1,1)=abs(G/(1+H_f_sum));
end

N_fft=length(signal);
n_fft=1:N_fft;
FFT_array=abs(fft(signal));
FFT_N2=floor(N_fft/2);
FFT_array=FFT_array(1:FFT_N2);
nFFT=(0:(FFT_N2-1))/FFT_N2*fs/2;%程Θだ繵瞯
FFT_test = H_f(:,1)*max(FFT_array)/max(H_f(:,1));

[num,locs] = findpeaks(FFT_test);
FreqNum = length(locs);
Lpc_Formant = zeros(FreqNum,2); %畃
peak_count = 1;
for i = 1:FreqNum
    if (FFT_test(locs(i)) > TH)
        Lpc_Formant(peak_count,1) = n_lpc_freq(locs(i));
        Lpc_Formant(peak_count,2) = num(i);
        peak_count=peak_count+1;
    end
end
Lpc_Formant(Lpc_Formant(:,1) == 0,:) = [];
% 
% figure;
% plot(nFFT,FFT_array,'r');
% xlabel('Frequency (Hz)');
% ylabel('Amplitude');
% set(gca,'FontWeight','bold','fontsize',10)
% hold on;
% plot(n_lpc_freq,H_f(:,1)*max(FFT_array)/max(H_f(:,1)),'LineWidth',2);%蹈絬
% % title('蹈絬');
% hold off;

% figure;
% plot(n_lpc_freq,FFT_test,'LineWidth',2);
% xlabel('Frequency (Hz)');
% ylabel('Amplitude');
% title('(b) Voiceless Sound');
% set(gca,'FontWeight','bold','fontsize',10)
% set(gcf,'unit','normalized','position',[0.2,0.2,0.29,0.14]);

% xlabel(Lpc_Formant);
% hold on;
% plot(n_lpc_freq,LPC_Peak(:,1),'r','linewidth',2);
% hold off;
