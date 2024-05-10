from pprint import pprint
import re

def full_gs_test():
    yti0 = {
        'title': '【スマブラSP】VIP連勝', 
        'duration': 10470, 'channel': 'Ly', 'release_timestamp': 1605536315, 'original_url': 'https://www.youtube.com/watch?v=0lSvRsCxnPs', 'fps': 60,
        'cap': 'https://rr3---sn-oguesnde.googlevideo.com/videoplayback?expire=1712399078&ei=hs4QZtemL5SB2roPvr2ssAY&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-APvt53FNKjbj6w3WAEGitLTVcMOG0SQx9-6q5RHHmcQ2&itag=299&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=yt&mm=31%2C29&mn=sn-oguesnde%2Csn-ogueln66&ms=au%2Crdu&mv=m&mvi=3&pl=36&initcwndbps=1227500&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=6615048940&dur=10470.033&lmt=1673241629628775&mt=1712377007&fvip=1&keepalive=yes&fexp=51141541&c=IOS&txp=7216224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRgIhAN9kM9UnxQwROa7whTwsHsbFyUYaoSSbaAwoKVww14RxAiEAy_7iQaPUhbeRP1ioMKJsCbr3WtE5zNPTAzDAbRUdWlA%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRAIgfGLeOJVykKMg1kNMoSqqULt3WIiv0wB_8dQKiJ3IFF8CIBQJkc7L6GUSEv_kgX-ksuCtIZmLwis-2dImLRhz2c6n'
    }
    yti1 = {
        'title': '【スマブラSP】ベレトスとカムイの道を切り開くVIP',
        'duration': 10928, 'channel': 'Ly', 'release_timestamp': 1605795535, 'original_url': 'https://www.youtube.com/watch?v=p3Ch2_bnhDE', 'fps': 60,
        'cap': 'https://rr5---sn-ogul7n7z.googlevideo.com/videoplayback?expire=1712399081&ei=ic4QZqqOF_zw2roPo-u9qAY&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-APmLSVWhTv3clPaAHyvHdrfY6qsmlm2HLlvF0AN3Wv2m&itag=303&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=Z_&mm=31%2C26&mn=sn-ogul7n7z%2Csn-npoeener&ms=au%2Conr&mv=m&mvi=5&pl=36&initcwndbps=1338750&siu=1&vprv=1&svpuc=1&mime=video%2Fwebm&gir=yes&clen=5119964032&dur=10927.728&lmt=1605905013438332&mt=1712377007&fvip=3&keepalive=yes&fexp=51141541&c=IOS&txp=5316222&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRgIhAP8Xv-kNl0548JIl_C1TQMkjPVEVaPSkqa8uYk2zFn6iAiEA6u97vvHuKwTbVWjbnTlhalLhB57kijI79DqPfWSeigY%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRQIhAPBkJd9k3wvYE1OcdkgTdOIypZqc0mQBs_x2lGyFyrBAAiAUGACgtJjmyGBnu2wmAgGKBfyGyrqysowfgn61l8H9qA%3D%3D'
    }
    yti2 = {
        'title': '【スマブラSP】カムイとベレスでVIP連勝目指す', 
        'duration': 10060, 'channel': 'Ly', 'release_timestamp': 1608034415, 'original_url': 'https://www.youtube.com/watch?v=dqs-pK0JhuI', 'fps': 60, 
        'cap': 'https://rr5---sn-ogul7n76.googlevideo.com/videoplayback?expire=1712399083&ei=i84QZsmSKpG02roP_MqA2AY&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-AFbA4kbrJXKdtjd5ZnRrSQKsOX-yNJN0udAaanG7DRvz&itag=303&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=kV&mm=31%2C29&mn=sn-ogul7n76%2Csn-oguelnzl&ms=au%2Crdu&mv=m&mvi=5&pl=36&initcwndbps=1427500&siu=1&vprv=1&svpuc=1&mime=video%2Fwebm&gir=yes&clen=4288148919&dur=10059.999&lmt=1608161189985301&mt=1712377007&fvip=4&keepalive=yes&fexp=51141541&c=IOS&txp=5316222&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRAIgRi_HoDB0fr3IfnSTCjqyDnHluYfn2rgu5frcFMqHW80CIDVNvUFGP8FmT2VbPNZ2x4ijoWJr8zl23UFsay-5viHg&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRgIhAOX_Yo_8t0SMHkbmbCTGpGtdVhcUqbn2k0Qk8N_K2bjNAiEA_i5K8AY7Zv3SHIoDNlI72-C-BgZcSA2sQYLCLar4tek%3D'
    }
    yti3 = {
        'title': '【スマブラSP】カムイでVIP連勝目指す\u30000連勝～',
        'duration': 6846, 'channel': 'Ly', 'release_timestamp': 1610886646, 'original_url': 'https://www.youtube.com/watch?v=Tpg6JuxtySU', 'fps': 60,
        'cap': 'https://rr2---sn-ogul7n7k.googlevideo.com/videoplayback?expire=1712399085&ei=jc4QZoyhNfKq0-kPrNe-sAs&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-AMYrTVygGlDBGWOlsCSf8mLXeueABAMQ9W9iSvFRRivF&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=Mn&mm=31%2C29&mn=sn-ogul7n7k%2Csn-oguelnsz&ms=au%2Crdu&mv=m&mvi=2&pl=36&initcwndbps=1205000&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=2544293804&dur=6846.033&lmt=1688209037491638&mt=1712377007&fvip=1&keepalive=yes&fexp=51141541&c=IOS&txp=7206224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRAIgXaXVfN5RDYnVP8JcHofnBt0gETioOu6rXMp6cQ0CStgCIEhFuYI0i9N4UHUFtZwjdp348kQWonT21hvH5TSGjcU_&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRgIhAKJn6krBTZ8cQWOsvPJQ5GQw0SFU76bp3MeXSawh1tqeAiEAhno35PjBcvCC7JQb3r5T-XpbxGcYZbq8gUsDCa6OW9k%3D'
    }
    yti4 = {
        'title': '【スマブラSP】連勝したいVIP配信（カムイ/ベレス）', 
        'duration': 9814, 'channel': 'Ly', 'release_timestamp': 1611404502, 'original_url': 'https://www.youtube.com/watch?v=_pYOceaWgUE', 'fps': 60, 
        'cap': 'https://rr1---sn-oguelnzr.googlevideo.com/videoplayback?expire=1712399088&ei=kM4QZr_pAuKy2roPz5ewuAc&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-AGPx8vzmSr4SJ_9R9b8injJ6LP8X6D1rmAKNMQxPPSR5&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=sC&mm=31%2C26&mn=sn-oguelnzr%2Csn-npoe7nlz&ms=au%2Conr&mv=m&mvi=1&pl=36&initcwndbps=1338750&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=3604320899&dur=9814.033&lmt=1688357023464874&mt=1712377007&fvip=1&keepalive=yes&fexp=51141541&c=IOS&txp=7206224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRAIgUX_XGKZwYhWW7dKlpRced1rP58sTra2MjemPDx7yUB0CIFYkVwEhGB8fRnM5g0rE83v5y_90DLRvpT6gOnN4AKUl&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRAIgagu7wrwX3D0_lm-ZqLOMO33zOI7xjuTdGmahJgnw7MYCIDNrlIK8vaE5RFMnQqjBD5_7mWHWrJZpLTahmSZ1xkVm'
    }
    yti5 = {
        'title': '【スマブラSP】VIP', 
        'duration': 9160, 'channel': 'Ly', 'release_timestamp': 1614436098, 'original_url': 'https://www.youtube.com/watch?v=rweC6vZ4nqY', 'fps': 60, 
        'cap': 'https://rr5---sn-oguelnz7.googlevideo.com/videoplayback?expire=1712399090&ei=ks4QZryNEOux2roPv_ygkAU&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-ADdwxAd_vOHxkJdar2BHYD5aaoGP6AD-37lKpKRtcPsH&itag=302&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=iy&mm=31%2C29&mn=sn-oguelnz7%2Csn-ogul7n7s&ms=au%2Crdu&mv=m&mvi=5&pl=36&initcwndbps=1345000&siu=1&vprv=1&svpuc=1&mime=video%2Fwebm&gir=yes&clen=2779864166&dur=9160.000&lmt=1614498325623127&mt=1712377247&fvip=4&keepalive=yes&fexp=51141541&c=IOS&txp=5316224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRAIgHkCI-5kkXmMCsUq6UFkOz-_Wrgc3z0YVwJIhl90agFcCIGkhDtvvL_-JbV0bXvzlUtHZSH89O7gn8weOkGsLaMSf&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRAIgT4ScRbpUu06HaT5D3saTQ7wjbLLvkl6m3FIeskLB0ncCIDGmdqVXHneuTbW69Sx6ZNm1h89EhpWaaE1llCWtaR20'
    }
    yti6 = {
        'title': '【スマブラSP】カムイやベレスでメイト1805～', 
        'duration': 8462, 'channel': 'Ly', 'release_timestamp': 1614597145, 'original_url': 'https://www.youtube.com/watch?v=ys5m64edPIM', 'fps': 60, 
        'cap': 'https://rr5---sn-oguesndl.googlevideo.com/videoplayback?expire=1712399092&ei=lM4QZuahGbXJ2roPkLGmqAY&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-AP88baxeXjy7Nb2PeTt1jxengjxSBavKqGH9BDpNrtUv&itag=302&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=2W&mm=31%2C26&mn=sn-oguesndl%2Csn-npoldn7s&ms=au%2Conr&mv=m&mvi=5&pl=36&initcwndbps=1205000&siu=1&vprv=1&svpuc=1&mime=video%2Fwebm&gir=yes&clen=2497038195&dur=8462.000&lmt=1614636578918737&mt=1712377007&fvip=5&keepalive=yes&fexp=51141541&c=IOS&txp=5316224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIhAKWO2onSg0BHhRj-OfjHAmaR15-z27ZG0qpLW71X_5gUAiATrsAFvR2UidX06BdmrF0O-scYWAoDMqmYkC8t7PljEg%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRQIgJoJ5-IYDGJS-FwKVJXLZ-o8IK38DT6rSEGxxh9EITJ0CIQChVdGG1ach49GRgThdlDcl-S1QzKKiOZi1XZ9HpMKwCQ%3D%3D'
    }
    yti7 = {
        'title': '【スマブラSP】猛者たちに揉まれながらスマメイト', 
        'duration': 8626, 'channel': 'Ly', 'release_timestamp': 1619598684, 'original_url': 'https://www.youtube.com/watch?v=xKp81GIaD6o', 'fps': 60, 
        'cap': 'https://rr4---sn-oguesnds.googlevideo.com/videoplayback?expire=1712399094&ei=ls4QZsLrHOW20-kPkNOg4AQ&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-ACelzFyWBawyTuxk2X-wDTM09ckx4kCTXCTGhgVKcqfK&itag=302&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=KD&mm=31%2C29&mn=sn-oguesnds%2Csn-oguelnss&ms=au%2Crdu&mv=m&mvi=4&pl=36&initcwndbps=1338750&siu=1&vprv=1&svpuc=1&mime=video%2Fwebm&gir=yes&clen=2565240500&dur=8625.800&lmt=1619637608087923&mt=1712377007&fvip=2&keepalive=yes&fexp=51141541&c=IOS&txp=5316224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIhAI3y_xDNDc-GXcDm6lc6o8rjwAgZXkp1GixH9-tJ8o7qAiAhGj_5M61-kSJ9kngzcvBcqgrbCWFE5OD04jmhHf31uQ%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRAIgIBzlDay4e7CH6-ZvsUgOzrW4JMiYPnxo8OmBy8SnooACIBM4ddYktdpMA91bQSmIwvEDv8z1t9lqKuqW3dR6bOqV'
    }
    yti8 = {
        'title': 'タミスマチャレンジ', 
        'duration': 9186, 'channel': 'Ly', 'release_timestamp': 1620124480, 'original_url': 'https://www.youtube.com/watch?v=G1UFDlHvs9Q', 'fps': 60, 
        'cap': 'https://rr4---sn-ogul7ne6.googlevideo.com/videoplayback?expire=1712399096&ei=mM4QZsC9Kde30-kPntyTSA&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-AAYoww9XDQ8xFxwoRtxmGTpi6S8zt_5OxmEhz1w0jYho&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=tZ&mm=31%2C26&mn=sn-ogul7ne6%2Csn-npoldn7s&ms=au%2Conr&mv=m&mvi=4&pl=36&initcwndbps=1345000&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=3370146057&dur=9185.833&lmt=1707157980777008&mt=1712377247&fvip=4&keepalive=yes&fexp=51141541&c=IOS&txp=7209224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIhAKzllmuJHOkwysSR6Xyae_IMOMtpuY-NUgAv1J4zLhuxAiBsUx4fcE5uOjYyvZwvMIVbPm5CeFs-eAmZOltQd8ib8Q%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRAIgUL1XuSEurX0UeaoQQjy7p1Lk1lRvNYgCYHDUl-6QkgoCIEFEa9hnCiCrp422nUAUgWN_2zCmNx6XZ_2m76dId8yT'
    }
    yti9 = {
        'title': '【スマブラSP】カムイやベレトスをつかう連勝VIP', 
        'duration': 8305, 'channel': 'Ly', 'release_timestamp': 1621087643, 'original_url': 'https://www.youtube.com/watch?v=jBPL8Ww_wDU', 'fps': 60, 
        'cap': 'https://rr2---sn-oguelnlz.googlevideo.com/videoplayback?expire=1712399098&ei=ms4QZo2WMtjt2roPo72psAY&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-AGJ1NLnVz7AQ0sN2r0ly7RgA3N0QWAE-jEBFvAAt6Z1v&itag=302&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=9L&mm=31%2C29&mn=sn-oguelnlz%2Csn-oguesnds&ms=au%2Crdu&mv=m&mvi=2&pl=36&initcwndbps=1338750&siu=1&vprv=1&svpuc=1&mime=video%2Fwebm&gir=yes&clen=2518889240&dur=8304.599&lmt=1621125718572127&mt=1712377007&fvip=4&keepalive=yes&fexp=51141541&c=IOS&txp=5316224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRgIhAMRUCcLKf5v4MQoV0x3kmfnRZjQTDSUfebvUy2L1QL8hAiEAiarokAZv7rmBeVUixheBAJA-JxethhTRrP4EbmLqXDE%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRQIgHPN6Zg10zQQ-iFWmdjMbI6xX-8_RJPRN3t-O3ggRjgkCIQDU5sRWwSkJd54Ambefe3lgXKxPO8gDQwrn2PAbOJBwbw%3D%3D'
    }
    yti10 = {
        'title': 'VIP連勝40～', 
        'duration': 13030, 'channel': 'Ly', 'release_timestamp': 1622462894, 'original_url': 'https://www.youtube.com/watch?v=P7Olxt1_tG0', 'fps': 60, 
        'cap': 'https://rr3---sn-oguesndz.googlevideo.com/videoplayback?expire=1712399100&ei=nM4QZs2zOKqD2roPsvizoAU&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-ANPLudL4-Du4mAGOhquENAUT_1KjMQzn49sVbxyi1713&itag=302&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=Vm&mm=31%2C29&mn=sn-oguesndz%2Csn-oguelnzy&ms=au%2Crdu&mv=m&mvi=3&pl=36&initcwndbps=1427500&siu=1&vprv=1&svpuc=1&mime=video%2Fwebm&gir=yes&clen=3631245386&dur=13029.399&lmt=1622679225862723&mt=1712377007&fvip=4&keepalive=yes&fexp=51141541&c=IOS&txp=5432434&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIhANAdaBcRlFMFIRhFQ9W4tsfJ7sFuW-Df2CknqmwkkPg9AiAIfB4G4ppPdjlih7OBgrtmSixyX5GI_S-7kU1_kD-oqA%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRAIgBp-zNCwVRmVeyZ1Fg4j_Xhwv_aW7f7HcrotuMme9T_sCIG-oQhQvF2VLe30DE1nM4n_1UaBkxhBaeob7km_k1L5u'
    }
    yti11 = {
        'title': '配信テストがてらVIP', 
        'duration': 4447, 'channel': 'Ly', 'release_timestamp': 1623148657, 'original_url': 'https://www.youtube.com/watch?v=wxySmIhgtnI', 'fps': 60, 
        'cap': 'https://rr3---sn-oguelnzz.googlevideo.com/videoplayback?expire=1712399103&ei=n84QZpGVDYH92roPyoyO6AY&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-AEb-PK_KjB3vDXGHI7MyE9dlNohe7_PstmwkoJToGVD7&itag=302&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=0k&mm=31%2C29&mn=sn-oguelnzz%2Csn-ogul7n7k&ms=au%2Crdu&mv=m&mvi=3&pl=36&initcwndbps=1345000&siu=1&vprv=1&svpuc=1&mime=video%2Fwebm&gir=yes&clen=1191955146&dur=4447.200&lmt=1623280045334794&mt=1712377247&fvip=2&keepalive=yes&fexp=51141541&c=IOS&txp=5316224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIgb3adfLlHCRpUjeD12UN3BL7qZO5_3RDKXnM9daZ-wCACIQDcXRmLDjTOFG9Ttgdp45b0pvtpDC1nPQIWW7O4viq2rw%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRAIgQBjZPQzWh_HcUkJvJuXrAcd1iA17Oi4-ceLRjA4VfG8CIEykcGESdg0gBNkV9HQM-7TUE4yIZwBqEblKl2jkhnZj'
    }
    yti12 = {
        'title': 'メイト レート2000目指してみる', 
        'duration': 17758, 'channel': 'Ly', 'release_timestamp': 1627381803, 'original_url': 'https://www.youtube.com/watch?v=Xk28pn-xRwc', 'fps': 60, 
        'cap': 'https://rr4---sn-oguesn6r.googlevideo.com/videoplayback?expire=1712399105&ei=oc4QZtinGoCt2roP2bOr8Ao&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-AAQc6FSOVo9w2E_afBjCvU7YygXBEQcMbH9d3041k5YE&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=oc&mm=31%2C29&mn=sn-oguesn6r%2Csn-oguelnsk&ms=au%2Crdu&mv=m&mvi=4&pl=36&initcwndbps=1631250&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=6520670246&dur=17757.464&lmt=1686223383242689&mt=1712377247&fvip=3&keepalive=yes&fexp=51141541&c=IOS&txp=7216224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRAIgNpB6ZAvZ0lLXYJVnRVbfla2ljK31paK9O7jJGzr8m4ACIBGwuHFFX0j7cpAu5VdPLGyZ7Rs2NEZtpwIV6sElWOHB&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRgIhAN5WumYHc9FGBvkSykh4WHWap97Lcok1cpEL2NcQJ8KyAiEAwKb2j6PCSI1dduKAQMUPm_pT5o-DRSmY359cuiUI6qQ%3D'
    }
    yti13 = {
        'title': '寝る前のスマメイト', 
        'duration': 14703, 'channel': 'Ly', 'release_timestamp': 1637336746, 'original_url': 'https://www.youtube.com/watch?v=pTmwLr8pl18', 'fps': 60, 
        'cap': 'https://rr1---sn-oguelnsr.googlevideo.com/videoplayback?expire=1712399107&ei=o84QZoXJJsOz2roPm8Oc0AM&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-AG6iZ4QsQa3QzVMhQ_5PaLZOVxHjF-ePeffhYLtma4fs&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=wu&mm=31%2C26&mn=sn-oguelnsr%2Csn-npoe7nz7&ms=au%2Conr&mv=m&mvi=1&pl=36&ctier=A&pfa=5&initcwndbps=1451250&hightc=yes&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=5713297475&dur=14702.598&lmt=1709324465792439&mt=1712377247&fvip=1&keepalive=yes&fexp=51141541&c=IOS&txp=7219224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Cctier%2Cpfa%2Chightc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRAIgb-bPiekL8QVxa40VQagKA4EbM2JNsh2fEUIuD85otfYCIEDCvW4dVkHgNIKz_4B8gIoAKZFM6qPHvRGI1-uyd3tx&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRQIgJopIO2YERxo4mKqa-ujCCNsjM4rpEzyteIIv3CoE13oCIQDzSsun5PeZUhSjat-StRzFlg96LfS-IoWhfMW6AbWKJQ%3D%3D'
    }
    yti14 = {
        'title': '篝火おつでした～VIPやる', 
        'duration': 6477, 'channel': 'Ly', 'release_timestamp': 1641816548, 'original_url': 'https://www.youtube.com/watch?v=geBNz25nqeo', 'fps': 60, 
        'cap': 'https://rr3---sn-oguelnzr.googlevideo.com/videoplayback?expire=1712399110&ei=ps4QZqeTAZz72roP-LW3-Ao&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-AIE83k-ktsd7q-baUBGZuP3fHUaUewYHGa4Ln4fDeeEF&itag=302&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=TK&mm=31%2C26&mn=sn-oguelnzr%2Csn-npoe7ned&ms=au%2Conr&mv=m&mvi=3&pl=36&initcwndbps=1451250&siu=1&vprv=1&svpuc=1&mime=video%2Fwebm&gir=yes&clen=1969897555&dur=6476.633&lmt=1641855732856248&mt=1712377247&fvip=2&keepalive=yes&fexp=51141541&c=IOS&txp=5316224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIhANbgM6XcJIeTR5JPhiigQ899-u6zF2Pw3hXPHyYiRNelAiBsaWki--OKuJUirHPObO_hCllFbwI6kURYD0DcgA-diw%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRQIhAKlhIQBTSKoN0COSMPmrIL5cP2eRui8UZ80TKcCwflrDAiB5hXcNJTVN-ew68-QdbwN4IKJSbe9yFe0o-L4rnkxvuQ%3D%3D'
    }
    yti15 = {
        'title': '2200を目指すスマメイト2095～', 
        'duration': 20371, 'channel': 'Ly', 'release_timestamp': 1645535403, 'original_url': 'https://www.youtube.com/watch?v=SvcsVDJ0P4E', 'fps': 60, 
        'cap': 'https://rr4---sn-oguesnds.googlevideo.com/videoplayback?expire=1712399112&ei=qM4QZq-OCcmA2roPtpibsAk&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-AMJuiYVk5qOGwOgw8Wpt3XgXzD08hcmJEOLIILAhScs5&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=96&mm=31%2C26&mn=sn-oguesnds%2Csn-npoe7ns6&ms=au%2Conr&mv=m&mvi=4&pl=36&initcwndbps=1345000&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=8082011690&dur=20370.566&lmt=1707700651663691&mt=1712377247&fvip=5&keepalive=yes&fexp=51141541&c=IOS&txp=7209224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIgavU2oLpvmMNqQjXNwad1yG1gyYkOpwwSlr5K4E2HT2ACIQCXUrrj3bE7w7CfbKzb6LAPbk4y2YsN6CLY8HWGLfXgDQ%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRAIgQc6P5ubUBM2UKbohyjUTa0B8BrH-nifrhWju3Q7GtxgCIGm3OumkSS7ux52yIoa7KB1RkgToobwMshmsbEVRoh7c'
    }
    yti16 = {
        'title': '2200を目指すスマメイト2112～', 
        'duration': 17238, 'channel': 'Ly', 'release_timestamp': 1645599910, 'original_url': 'https://www.youtube.com/watch?v=oMhuTTOL0Vc', 'fps': 60, 
        'cap': 'https://rr3---sn-oguelnsk.googlevideo.com/videoplayback?expire=1712399114&ei=qs4QZoydEsu_0-kPwZC3qAY&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-AFd2B-9HTkc-GP7Vp0l_gryZYzMvxbf6ajRYv4DWslKR&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=F-&mm=31%2C26&mn=sn-oguelnsk%2Csn-npoe7nsk&ms=au%2Conr&mv=m&mvi=3&pl=36&initcwndbps=1345000&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=6832390087&dur=17237.566&lmt=1688638051466574&mt=1712377247&fvip=5&keepalive=yes&fexp=51141541&c=IOS&txp=7209224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIgQ7qt77BIxJd8Do39t8hkza9jaVMsqq8h9OanM720IysCIQCdEuk8Wjqn6DBKgo9ovhXU-3fDFdV5z0_nBT9NfS1Tuw%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRQIhAPqb3W9FbgT3t6DWDt1CAVW_QGtJ7UErgdGDPBSTjuSMAiAXRp06TdMnH_FlyF_TWg8KTYNKUxoXvTTUCvecDoysJw%3D%3D'
    }
    yti17 = {
        'title': 'だらだらVIP連勝\u300020~', 
        'duration': 9624, 'channel': 'Ly', 'release_timestamp': 1653553782, 'original_url': 'https://www.youtube.com/watch?v=KZREZ0nU_ps', 'fps': 60, 
        'cap': 'https://rr4---sn-oguelnsk.googlevideo.com/videoplayback?expire=1712399116&ei=rM4QZquBG8mq2roP5vSd0A0&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-AGU7VhA9KpxORchG5zU3VE_zJPpVZzJ1LZoEEEQ-QIGT&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=GP&mm=31%2C29&mn=sn-oguelnsk%2Csn-ogul7n7k&ms=au%2Crdu&mv=m&mvi=4&pl=36&initcwndbps=1293750&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=3660241957&dur=9623.999&lmt=1707443740973267&mt=1712377247&fvip=1&keepalive=yes&fexp=51141541&c=IOS&txp=7209224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIhAPuXEVczEwFZhX2tG_HCo-63GBniSBQo42F1TrQjcrMVAiBR84_m7QpyNfVuQ6rupfzD8Yu22_5H_myXE5Jvh0VlPQ%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRgIhAIFQlZZtUWRKRT3kVossbGsI-qwoqjWd13mfKvqzl2flAiEA4FhAtr7AVSyYi9rn63K5YHeE8t5ZyNU0ZTHg3HyeEB0%3D'
        }
    yti18 = {
        'title': 'VIP連勝めざす', 
        'duration': 11911, 'channel': 'Ly', 'release_timestamp': 1655286515, 'original_url': 'https://www.youtube.com/watch?v=9p-st5RNB2M', 'fps': 30, 
        'cap': 'https://rr4---sn-oguesnde.googlevideo.com/videoplayback?expire=1712399118&ei=rs4QZvD6Ks622roP_r6usAY&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-APsVsWgoDAfzRedEsj_cdi0PWdvttvZ5mSLp1gMENP8F&itag=136&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=qj&mm=31%2C26&mn=sn-oguesnde%2Csn-npoe7nez&ms=au%2Conr&mv=m&mvi=4&pl=36&initcwndbps=1345000&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=2816094138&dur=11910.565&lmt=1690121981204678&mt=1712377247&fvip=2&keepalive=yes&fexp=51141541&c=IOS&txp=7209224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIgXzq-pNnhoL5hR-N77jIAAsQHySUXYV_VPChnqLgKYSICIQCg3CyMREh07CBwMjiMsjpBcpkC1D1ohdIntRGDjlxrvA%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRQIgFx5vrMoDs_6UGgXUN8pjsF8-Nsu3zIlewILTK8LEzK4CIQC0bdRbNpA_oV2FWQ71CUiqxexs0Rih9V62YE9fgYFL1g%3D%3D'
    }
    yti19 = {
        'title': 'ざつだんVIP', 
        'duration': 4206, 'channel': 'Ly', 'release_timestamp': 1668353018, 'original_url': 'https://www.youtube.com/watch?v=Pkho2QJ2bfw', 'fps': 30, 
        'cap': 'https://rr2---sn-oguesnds.googlevideo.com/videoplayback?expire=1712399120&ei=sM4QZqi_MbHu2roPt4ij8Ag&ip=240b%3A11%3A1041%3A8a00%3Ae56b%3Abeee%3A62f8%3A5519&id=o-AJ7vYbfZNGI8oq2Eml-IbjG_HguGkWFfatFMKsXlfc3t&itag=136&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=-H&mm=31%2C29&mn=sn-oguesnds%2Csn-oguelnzz&ms=au%2Crdu&mv=m&mvi=2&pl=36&initcwndbps=1631250&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=1000217102&dur=4205.866&lmt=1707601395192016&mt=1712377247&fvip=3&keepalive=yes&fexp=51141541&c=IOS&txp=7219224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRAIgeV5fs3Epl0nC_anwtPrFmcO1Ds4EiroCLybgKLymd8cCIBGvZUJoubdBwABP4vyUUooEzToaDkx3jtJ-4zsy-i-w&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRgIhALWDV7erBfauL4p3-fIzxipZR7OzwCmXI4UonkKGa3jrAiEAxkqwtk64M4L0bxC1hR3oKixJEgy6rJOWuewUiDWEWyk%3D'
    }
    # return ['KAMUI', 'BYLETH'], [yti0, yti1, yti2, yti3, yti4, yti5, yti6, yti7, yti8, yti9, yti10, yti11, yti12, yti13, yti14, yti15, yti16, yti17, yti18, yti19], {'crop0': {'pt1': [0,0], 'pt2': [1920,1080]}}
    return ['KAMUI', 'BYLETH'], [yti0], {'crop0': {'pt1': [0,0], 'pt2': [1920,1080]}}

def part_gs_test():
    yti0 = {
        'title': '【スマブラSP】VIP→トレモ', 
        'duration': 5496, 'channel': 'Neo', 'release_timestamp': 1630295308, 'original_url': 'https://www.youtube.com/watch?v=9wFfGMbNuIg', 'fps': 60, 
        'cap': 'https://rr5---sn-oguelnsr.googlevideo.com/videoplayback?expire=1712083324&ei=HP0LZqWYBOzr2roP_Pe0sAY&ip=106.73.16.65&id=o-AB-392f_drUAAqdqYV3T_Gdz7w-9qnVKhD_9_GCRvTRv&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=qd&mm=31%2C29&mn=sn-oguelnsr%2Csn-oguesn6r&ms=au%2Crdu&mv=m&mvi=5&pl=16&initcwndbps=846250&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=1898594811&dur=5496.233&lmt=1674517743193918&mt=1712061202&fvip=4&keepalive=yes&fexp=51141541&c=IOS&txp=7216224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRgIhAJsAKyuiOUpqyIG-LXVC6iMnjYIPdANrgUMUVj8VyQlaAiEA4-ctl788BHcEhCAWyahFC7MKcPULsKktS7Xf4wzryTw%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRgIhALW0VGBZv8qNO4zZHTS26wvEN4hXFuumh5UCVd3DTYlIAiEAzSLyJu_c65j75IPyL9MEM7ZxUZsWZyTBNV405rNHULM%3D'
    }
    yti1 = {
        'title': '【スマブラSP】VIP 連勝\u3000負けたら辞める', 
        'duration': 3665, 'channel': 'Neo', 'release_timestamp': 1630548488, 'original_url': 'https://www.youtube.com/watch?v=xU1BLJ9gZ7I', 'fps': 60, 
        'cap': 'https://rr3---sn-oguesndl.googlevideo.com/videoplayback?expire=1712083326&ei=Hv0LZrSmEeuF2roP8I2c2Ao&ip=106.73.16.65&id=o-AJU0BRpcOCkVFgBSu1gFF5JbIknCsC_KyhzWOhPlbKfl&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=ic&mm=31%2C29&mn=sn-oguesndl%2Csn-oguelnz7&ms=au%2Crdu&mv=m&mvi=3&pl=16&initcwndbps=923750&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=1367839480&dur=3664.433&lmt=1671856597725800&mt=1712061202&fvip=4&keepalive=yes&fexp=51141541&c=IOS&txp=7216224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIhAKL0YeIGTCB41ruVBR_T63B5ES6sXJWMLec_qAhEUxv9AiAU9bsrta9OWYElUI4CfdIwwM4CnXdMoMCqsUtloxUEyQ%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRAIgJDHcI7EGbJSa1R1w8YLEwwaWBwztd9SWPaE1K3IK1M0CIB8a1sNhK3p_tfVbRHwehjuAPjhOXBD1ngPZZvT8HTIA'
    }
    yti2 = {
        'title': '【スマブラSP】すまめいと', 
        'duration': 5458, 'channel': 'Neo', 'release_timestamp': 1631176068, 'original_url': 'https://www.youtube.com/watch?v=cdTxb0a0jrA', 'fps': 60, 
        'cap': 'https://rr2---sn-ogul7n7z.googlevideo.com/videoplayback?expire=1712083328&ei=IP0LZouhE5yF0-kPjZWA4QE&ip=106.73.16.65&id=o-AEIdxzSYOmtrLkGdJq0H44dZFhH_ThcmwcFjrbMSffNa&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=zE&mm=31%2C29&mn=sn-ogul7n7z%2Csn-oguelnsl&ms=au%2Crdu&mv=m&mvi=2&pl=16&initcwndbps=923750&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=1889958743&dur=5457.716&lmt=1631225593097688&mt=1712061202&fvip=1&keepalive=yes&fexp=51141541&c=IOS&txp=7216222&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRgIhAKD5IJBSHNH6k0niQ9JxQ-cS0y69hl_sIqXM78Z9ImS7AiEA9-M1Cbfxu-TDx7zFG5ZZmPpIJ7J7HwAr0wwAW-BCIeE%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRQIgdtaRAGaZK6j0HBpSUCYB0at4-op84s_x6qVgSlAosmECIQCmMRlY5eQa22S98BjePcya6yF32yRR2ZTkZO8yC00Jcg%3D%3D'
    }
    yti3 = {
        'title': '【スマブラSP】すまめいと→vip', 
        'duration': 6677, 'channel': 'Neo', 'release_timestamp': 1633075410, 'original_url': 'https://www.youtube.com/watch?v=RAtI3Hl4weU', 'fps': 60, 
        'cap': 'https://rr5---sn-oguelnzl.googlevideo.com/videoplayback?expire=1712083330&ei=Iv0LZtn-Hpu12roP7_ql6Aw&ip=106.73.16.65&id=o-AFF3hMzc2FafMHM3ZfMXyzJkNMvMYipOROWQ2jq9nabA&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=RF&mm=31%2C26&mn=sn-oguelnzl%2Csn-npoe7nds&ms=au%2Conr&mv=m&mvi=5&pl=16&initcwndbps=846250&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=2279255606&dur=6677.232&lmt=1686068743330652&mt=1712061202&fvip=4&keepalive=yes&fexp=51141541&c=IOS&txp=7216224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIgNxAZCVpP6bb5HZtWpOBzWH64i2A1TYJr11p-5YS3XJACIQChP3r7WNB736PqtX7W5qvFWk4SM90OBszH0NsGFnT59A%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRgIhAKeJARs6jXIKC4rqhvY8tzp5ApCjUq6HSLUqeWTlk9WmAiEAlNsLxgYRoIZeVDgDr54S2P3rdPUtoG32hhnUEk01o44%3D'
    }
    yti4 = {
        'title': '【スマブラSP】カムイメイト', 
        'duration': 7955, 'channel': 'Neo', 'release_timestamp': 1654925784, 'original_url': 'https://www.youtube.com/watch?v=pRmmyRNcQk0', 'fps': 60, 
        'cap': 'https://rr4---sn-oguelnsy.googlevideo.com/videoplayback?expire=1712083332&ei=JP0LZom5GPjM2roPovyy0Ao&ip=106.73.16.65&id=o-AB4ohTaG48wEXwibot_hSOgy_WgMZE9USYb38lgjAK0T&itag=298&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&mh=-e&mm=31%2C26&mn=sn-oguelnsy%2Csn-npoe7nl6&ms=au%2Conr&mv=m&mvi=4&pl=16&initcwndbps=923750&siu=1&vprv=1&svpuc=1&mime=video%2Fmp4&gir=yes&clen=2485924475&dur=7955.150&lmt=1680509445822434&mt=1712061202&fvip=2&keepalive=yes&fexp=51141541&c=IOS&txp=7219224&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Csiu%2Cvprv%2Csvpuc%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRQIhAL2u4o1Jrw8LWKHK80anM6wvs6NqRjpQP7dNpkBjHHOvAiB93vWij6FqjG0jn9rPriGossY26ZI5pT8RxhK6_bSKzw%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALClDIEwRQIgMCCU2I-mEl-zDo98Y0wZvt9umxNzRd3as-r8Fh6V_zoCIQDSNbx7i3amzRcTPNHexJuG8lp-uacuhJIrxPgNmQpnNA%3D%3D'
    }
    return ['KAMUI'], [yti0, yti1, yti2, yti3, yti4], {'crop0': {'pt1': [0, 0], 'pt2': [1585, 891]}}

# def generate_message(k=10):
#     message_repeater = dict()
#     for i in range(5):
#         message_repeater.update({
#             f"images{i}": {
#                 "start_html": {
#                     "image_source": "static/image0_0.jpg",
#                     "inside_url": "url",
#                     "inside_vs": "vs"
#                 },
#                 "end_html": {
#                     "image_source": "static/image0_0.jpg",
#                     "inside_url": "url",
#                     "inside_res": "res"
#                 }
#             }
#         })
#     collect_repeater = dict()
#     for i in range(k):
#         collect_repeater.update({
#             f"message{i}": {
#                 "id": i,
#                 "text": "Not started",
#                 "visibility": False,
#                 "repeater": message_repeater
#             }
#         })
#     pprint(collect_repeater)

# def generate_message(state, collect_repeater=dict()):
def generate_message(collect_repeater=dict()):
    # for i in range(state["main_yt_num"]):
    for i in range(10):
        collect_repeater.update({
            f"message{i}": {
                "id": i,
                "text": "Not started",
                "visibility": False,
                "repeater": generate_view_results()
            }
        })
    # state["collect"]["repeater"] = collect_repeater
    pprint(collect_repeater)

# def generate_view_results(state, message_repeater=dict(), res_num=0):
def generate_view_results(message_repeater=dict(), res_num=0):
    message_repeater.update({
        f"images{res_num}": {
            "start_html": {
                "image_source": f"static/image{res_num}_0.jpg",
                "inside_url": "url",
                "inside_vs": "vs"
            },
            "end_html": {
                "image_source": f"static/image{res_num}_1.jpg",
                "inside_url": "url",
                "inside_res": "res"
            }
        }
    })
    # if res_num>0: state["collect"]["repeater"][f"message{res_num}"]["repeater"] = message_repeater
    return message_repeater

state_dict = {
    "collect": {
        "start_button": {
            "disabled": "no",
            #"visibility": False if rel else True
        },
        "stop_button": {
            "disabled": "yes",
            #"visibility": False if rel else True
        },
        "repeater": {
            "message0": {
                "id": 0,
                "text": "Not started",
                "visibility": False,
                "repeater": {
                    "images0": {
                        "start_html": {
                            "image_source": "static/image0_0.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image0_0.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images1": {
                        "start_html": {
                            "image_source": "static/image0_0_crop.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image0_0_crop.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images2": {
                        "start_html": {
                            "image_source": "static/image0_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image0_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    }
                }
            },
            "message1": {
                "id": 1,
                "text": "Not started",
                "visibility": False,
                "repeater": {
                    "images0": {
                        "start_html": {
                            "image_source": "static/image1_0.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image1_0.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images1": {
                        "start_html": {
                            "image_source": "static/image1_0_crop.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image1_0_crop.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images2": {
                        "start_html": {
                            "image_source": "static/image1_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image1_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    }
                }
            },
            "message2": {
                "id": 2,
                "text": "Not started",
                "visibility": False,
                "repeater": {
                    "images0": {
                        "start_html": {
                            "image_source": "static/image2_0.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image2_0.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images1": {
                        "start_html": {
                            "image_source": "static/image2_0_crop.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image2_0_crop.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images2": {
                        "start_html": {
                            "image_source": "static/image2_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image2_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    }
                }
            },
            "message3": {
                "id": 3,
                "text": "Not started",
                "visibility": False,
                "repeater": {
                    "images0": {
                        "start_html": {
                            "image_source": "static/image3_0.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image3_0.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images1": {
                        "start_html": {
                            "image_source": "static/image3_0_crop.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image3_0_crop.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    },
                    "images2": {
                        "start_html": {
                            "image_source": "static/image3_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_vs": "vs"
                        },
                        "end_html": {
                            "image_source": "static/image3_0_crop_3rect.jpg",
                            "inside_url": "url",
                            "inside_res": "res"
                        }
                    }
                }
            },
            "visibility": False
        },
        #"visibility": False if rel else True
    }
}

def none_check():
    print(len([None, None]))

if __name__ == '__main__':
    yt_infos = part_gs_test()[1]
    for i, yti in enumerate(yt_infos):
        yt_url = yti["original_url"]+"&t="+"3"*(i+1)+"s"
        print(yt_url)
        # 文字列から数字部分だけをリストとして取得：re.findall関数 https://atmarkit.itmedia.co.jp/ait/articles/2103/12/news030.html
        print(re.findall(r'\d+',yt_url)[-1])
    
    generate_message()
    none_check()