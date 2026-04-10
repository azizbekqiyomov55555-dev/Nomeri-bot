<?php
session_start();
date_default_timezone_set("Asia/Tashkent");
$time = date('H:i');
ob_start();

define('API_KEY', "8674893543:AAEmbCiJkWchGiSgXzXrcL_NYZRFl75GEbw");

$admin     = "8537782289";   // 1-admin
$admin2    = "8674893543";   // 2-admin
$admins    = [$admin, $admin2];  // admin massivi

$proof     = "@QoraCoders_Uzb";
$simkey    = "8395fA936b4874292c214df2A4c9Ae8c";
$simfoiz   = "50";
$simrub    = "130";
$channel   = "130";
$me        = "🛎";
$smm12     = "https://t.me/QoraCoders_Uzb/1";
$valyuta   = "so'm";
$paychannel = "@QoraCoders_Uzb";

// ─── DB ulanish ───────────────────────────────────────────────────
define("DB_SERVER",   "localhost");
define("DB_USERNAME", "YOUR_DB_USER");   // <-- o'zgartiring
define("DB_PASSWORD", "YOUR_DB_PASS");   // <-- o'zgartiring
define("DB_NAME",     "YOUR_DB_NAME");   // <-- o'zgartiring

$connect = mysqli_connect(DB_SERVER, DB_USERNAME, DB_PASSWORD, DB_NAME);
mysqli_set_charset($connect, "utf8mb4");

$bot = bot('getMe')->result->username;

// ─── YORDAMCHI FUNKSIYALAR ─────────────────────────────────────────

function enc($var, $exception){
    if($var=="encode") return base64_encode($exception);
    elseif($var=="decode") return base64_decode($exception);
}

function keyboard($a=[]){
    return json_encode(['inline_keyboard'=>$a]);
}

function api_query($s){
    $qas = ["ssl"=>["verify_peer"=>false,"verify_peer_name"=>false]];
    $c = file_get_contents($s, false, stream_context_create($qas));
    return $c ? $c : json_encode(['balance'=>" ?"]);
}

function arr($p){
    global $connect;
    $s = mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM `providers` WHERE id = $p"));
    $data = json_decode(file_get_contents($s['api_url']."?key=".$s['api_key']."&action=services"),1);
    $values=[]; $new_arr=[]; $co=0;
    foreach($data as $value){
        if(!in_array($value['category'],$new_arr)){
            $new_arr[]=$value['category'];
            $co++;
            $values[]=['id'=>$co,'name'=>$value['category']];
        }
    }
    $val=['count'=>$co,'results'=>$values];
    return $values ? json_encode($val) : json_encode(["error"=>1]);
}

function bot($method, $datas=[]){
    $url="https://api.telegram.org/bot".API_KEY."/".$method;
    $ch=curl_init();
    curl_setopt($ch,CURLOPT_URL,$url);
    curl_setopt($ch,CURLOPT_RETURNTRANSFER,true);
    curl_setopt($ch,CURLOPT_POSTFIELDS,$datas);
    $res=curl_exec($ch);
    if(curl_error($ch)) var_dump(curl_error($ch));
    else return json_decode($res);
}

function rmdirPro($path){
    $scan=array_diff(scandir($path),['.','..']);
    foreach($scan as $value){
        if(is_dir("{$path}/{$value}")) rmdirPro("{$path}/{$value}");
        else @unlink("{$path}/{$value}");
    }
    rmdir($path);
}

function trans($x){
    $e=json_decode(file_get_contents("http://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=uz&dt=t&q=".urlencode($x).""),1);
    return $e[0][0][0];
}

function number($a){
    return number_format($a,00,' ',' ');
}

function del(){
    global $cid,$mid,$chat_id,$message_id;
    return bot('deleteMessage',['chat_id'=>$chat_id.$cid,'message_id'=>$message_id.$mid]);
}

function edit($id,$mid,$tx,$m){
    return bot('editMessageText',[
        'chat_id'=>$id,'message_id'=>$mid,
        'text'=>"<b>$tx</b>",'parse_mode'=>"HTML",
        'disable_web_page_preview'=>true,'reply_markup'=>$m
    ]);
}

function sms($id,$tx,$m){
    return bot('sendMessage',[
        'chat_id'=>$id,'text'=>"<b>$tx</b>",
        'parse_mode'=>"HTML",'disable_web_page_preview'=>true,'reply_markup'=>$m
    ]);
}

function get($h){ return file_get_contents($h); }
function put($h,$r){ file_put_contents($h,$r); }

function generate(){
    $arr=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','R','S','T','U','V','X','Y','Z','1','2','3','4','5','6','7','8','9','0'];
    $pass="";
    for($i=0;$i<7;$i++) $pass.=$arr[rand(0,count($arr)-1)];
    return $pass;
}

function adduser($cid){
    global $connect;
    $result=mysqli_query($connect,"SELECT * FROM users WHERE id = $cid");
    $row=mysqli_fetch_assoc($result);
    if(!$row){
        $key=md5(uniqid()); $referal=generate();
        $rew=mysqli_num_rows(mysqli_query($connect,"SELECT * FROM users"));
        $new=$rew+1;
        mysqli_query($connect,"INSERT INTO users(`user_id`,`id`,`status`,`balance`,`outing`,`api_key`,`referal`) VALUES ('$new','$cid','active','0','0','$key','$referal');");
    }
}

function referal($hi){
    $daten=[]; $rev=[];
    $fayllar=glob("./user/*.*");
    foreach($fayllar as $file){
        if(mb_stripos($file,".users")!==false){
            $value=file_get_contents($file);
            $id=str_replace(["./user/",".users"],["",""],$file);
            $daten[$value]=$id; $rev[$id]=$value;
        }
    }
    asort($rev); $reversed=array_reverse($rev); $text="";
    for($i=0;$i<$hi;$i+=1){
        $order=$i+1; $id=$daten["$reversed[$i]"];
        $ism=bot('getChat',['chat_id'=>$id])->result->first_name;
        $text.="<b>{$order}</b>. <a href='tg://user?id={$id}'>{$ism}</a> - <code>".floor($reversed[$i])."</code> <b> ta</b>\n";
    }
    return $text;
}

function joinchat($id){
    global $connect;
    $array=["inline_keyboard"];
    $get=file_get_contents("set/channel");
    $ex=explode("\n",$get);
    if($get==null) return true;
    $uns=false;
    for($i=0;$i<=count($ex)-1;$i++){
        $first_line=$ex[$i]; $kanall=str_replace("@","",$first_line);
        $ret=bot("getChatMember",["chat_id"=>$first_line,"user_id"=>$id]);
        $stat=$ret->result->status;
        if(($stat=="creator" or $stat=="administrator" or $stat=="member")){
            $array['inline_keyboard']["$i"][0]['text']="✅ ".$first_line;
            $array['inline_keyboard']["$i"][0]['url']="https://t.me/$kanall";
        }else{
            $array['inline_keyboard']["$i"][0]['text']="❌ ".$first_line;
            $array['inline_keyboard']["$i"][0]['url']="https://t.me/$kanall";
            $uns=true;
        }
    }
    $array['inline_keyboard']["$i"][0]['text']="🔄 Tekshirish";
    $array['inline_keyboard']["$i"][0]['callback_data']="result";
    if($uns==true){
        bot('sendMessage',['chat_id'=>$id,'text'=>"⚠️ <b>Iltimos Botdan foydalanish uchun Homiy kanallarga obuna bo'ling:</b>",'parse_mode'=>"html",'reply_markup'=>json_encode($array)]);
    }else{
        return true;
    }
}

// ─── UPDATE PARSE ─────────────────────────────────────────────────

$update     = json_decode(file_get_contents('php://input'));
$message    = $update->message;
$mid        = $message->message_id;
$msgs       = json_decode(file_get_contents('msgs.json'),true);
$data       = $update->callback_query->data;
$type       = $message->chat->type;
$text       = $message->text;
$sd         = $message->text;
$uid        = $message->from->id;
$gname      = $message->chat->title;
$left       = $message->left_chat_member;
$new        = $message->new_chat_member;
$name       = $message->from->first_name;
$bio        = $message->from->about;
$repid      = $message->reply_to_message->from->id;
$repname    = $message->reply_to_message->from->first_name;
$newid      = $message->new_chat_member->id;
$leftid     = $message->left_chat_member->id;
$newname    = $message->new_chat_member->first_name;
$leftname   = $message->left_chat_member->first_name;
$username   = $message->from->username;
$cmid       = $update->callback_query->message->message_id;
$cusername  = $message->chat->username;
$repmid     = $message->reply_to_message->message_id;
$ccid       = $update->callback_query->message->chat->id;
$cuid       = $update->callback_query->message->from->id;
$from_id    = $message->from->id;
$chat_id    = $update->callback_query->message->chat->id;
$message_id = $update->callback_query->message->message_id;
$call       = $update->callback_query;
$mes        = $call->message;
$qid        = $call->id;
$callbackdata = $update->callback_query->data;
$callcid    = $mes->chat->id;
$callmid    = $mes->message_id;
$callfrid   = $call->from->id;
$calluser   = $mes->chat->username;
$callfname  = $call->from->first_name;
$photo      = $message->photo;
$gif        = $message->animation;
$video      = $message->video;
$music      = $message->audio;
$voice      = $message->voice;
$sticker    = $message->sticker;
$document   = $message->document;
$for        = $message->forward_from;
$for_id     = $for->id;
$contact    = $message->contact;
$nomer_id   = $contact->user_id;
$nomer_user = $contact->username;
$nomet_name = $contact->first_name;
$nomer_ph   = $contact->phone_number;
$edituz     = $update->callback_query->message->from->id;
$mesuz      = $update->callback_query->message->message_id;
$cid        = $message->chat->id;
$cidtyp     = $message->chat->type;
$miid       = $message->message_id;
$callback   = $update->callback_query;
$mmid       = $callback->inline_message_id;
$idd        = $callback->message->chat->id;
$cbid       = $callback->from->id;
$cbuser     = $callback->from->username;
$ida        = $callback->id;
$cqid       = $update->callback_query->id;
$cbins      = $callback->chat_instance;
$cbchtyp    = $callback->message->chat->type;
$cid2       = $chat_id;
$mid2       = $message_id;
$sana       = date("d/m/Y | H:i");

$botdel       = $update->my_chat_member->new_chat_member;
$botdel_id    = $update->my_chat_member->from->id;
$userstatus   = $botdel->status;

$step  = get("user/$cid.step");
$stepc = get("user/$chat_id.step");

// ─── ADMINNI TEKSHIRISH (massiv orqali) ───────────────────────────
// $cid yoki $chat_id $admins massivida bor-yo'qligini tekshirish uchun:
// in_array($cid, $admins)

// ─── DIREKTORIYALAR YARATISH ──────────────────────────────────────
@mkdir("user"); @mkdir("set"); @mkdir("odam");
@mkdir("foydalanuvchi"); @mkdir("foydalanuvchi/yurak");
@mkdir("foydalanuvchi/hisob"); @mkdir("foydalanuvchi/til");
@mkdir("donat"); @mkdir("donat/PUBGMOBILE"); @mkdir("donat/FreeFire");

// ─── DONAT NARXLARINI BOSHLASH ────────────────────────────────────
$pubg_prices = ["60uc"=>"12000","120uc"=>"24000","180uc"=>"36000","325uc"=>"63000",
    "385uc"=>"75000","660uc"=>"120000","720uc"=>"132000","985uc"=>"180000",
    "1320uc"=>"245000","1800uc"=>"340000","2125uc"=>"403000","2460uc"=>"470000",
    "3950uc"=>"770000","8100uc"=>"1440000"];
foreach($pubg_prices as $k=>$v){
    if(!file_get_contents("donat/PUBGMOBILE/$k.txt"))
        file_put_contents("donat/PUBGMOBILE/$k.txt",$v);
}
$ff_prices = ["100almaz"=>"12500","210almaz"=>"25000","530almaz"=>"60000","1080almaz"=>"120000","2200almaz"=>"240000"];
foreach($ff_prices as $k=>$v){
    if(!file_get_contents("donat/FreeFire/$k.txt"))
        file_put_contents("donat/FreeFire/$k.txt",$v);
}

foreach($pubg_prices as $k=>$v) $$k=file_get_contents("donat/PUBGMOBILE/$k.txt");
foreach($ff_prices as $k=>$v)   $$k=file_get_contents("donat/FreeFire/$k.txt");

if(!file_exists("foydalanuvchi/yurak/$cid.txt"))
    file_put_contents("foydalanuvchi/yurak/$cid.txt","0");
if(!file_exists("foydalanuvchi/hisob/$cid.til"))
    file_put_contents("foydalanuvchi/hisob/$cid.til","uz");

$pul  = get("user/$chat_id.pul");
$til  = file_get_contents("foydalanuvchi/hisob/$cid.til");
$step = get("user/$cid.step");

// ─── ASOSIY MENYULAR ──────────────────────────────────────────────
$ort = json_encode(['resize_keyboard'=>true,'keyboard'=>[[['text'=>"➡️ Orqaga"]]]]);
$aort = json_encode(['resize_keyboard'=>true,'keyboard'=>[[['text'=>"🗄️ Boshqaruv"]]]]);

$panel = json_encode(['resize_keyboard'=>true,'keyboard'=>[
    [['text'=>"⚙️ Asosiy sozlamalar"],['text'=>"📊 Statistika"]],
    [['text'=>"🔔 Xabar yuborish"],['text'=>"🛍 Chegirmalar"]],
    [['text'=>"👤 Foydalanuvchini boshqarish"]],
    [['text'=>"⏰ Cron sozlamasi"],['text'=>"📞 Nomer API balans"]],
    [['text'=>"🤖 Bot holati"],['text'=>"🎮 Donat sozlamalari"]],
    [['text'=>"⏪ Orqaga"]],
]]);

$panel2 = json_encode(['resize_keyboard'=>true,'keyboard'=>[
    [['text'=>"🛍 Buyurtmalarni sozlash"],['text'=>"📎 Majburiy obunalar"]],
    [['text'=>"💵 Kursni o'rnatish"],['text'=>"⚖️ Foizni o'rnatish"]],
    [['text'=>"📊 Buyurtmani tekshirish"],['text'=>"🤖 Bot tezligi"]],
    [['text'=>"🔑 API Sozlamalari"],['text'=>"⚙️ Boshqa sozlamalar"]],
    [['text'=>"🎟 Promokod"]],
    [['text'=>"🗄️ Boshqaruv"]],
]]);

$menu = json_encode(['resize_keyboard'=>true,'keyboard'=>[
    [['text'=>"🛍 𝔹𝕦𝕪𝕦𝕣𝕥𝕞𝕒 𝕓𝕖𝕣𝕚𝕤𝕙"],['text'=>"📞 ℕ𝕠𝕞𝕖𝕣 𝕠𝕝𝕚𝕤𝕙"]],
    [['text'=>"🔐 𝕄𝕖𝕟𝕚𝕟𝕘 𝕙𝕚𝕤𝕠𝕓𝕚𝕞"],['text'=>"💰 ℍ𝕚𝕤𝕠𝕓𝕟𝕚 𝕥𝕠'𝕝𝕕𝕚𝕣𝕚𝕤𝕙"]],
    [['text'=>"🛒 𝔹𝕦𝕪𝕦𝕣𝕥𝕞𝕒 𝕩𝕠𝕝𝕒𝕥𝕚"],['text'=>"🚀 ℝ𝕖𝕗𝕖𝕣𝕒𝕝 𝕪𝕚ğ𝕚𝕤𝕙"]],
    [['text'=>"☎️ 𝔸𝕕𝕞𝕚𝕟𝕚𝕤𝕥𝕣𝕒𝕥𝕠𝕣"],['text'=>"🤝 ℍ𝕒𝕞𝕜𝕠𝕣𝕝𝕚𝕜 (𝔸ℙ𝕀)"]],
]]);

$menu_p = json_encode(['resize_keyboard'=>true,'keyboard'=>[
    [['text'=>"🛍 𝔹𝕦𝕪𝕦𝕣𝕥𝕞𝕒 𝕓𝕖𝕣𝕚𝕤𝕙"],['text'=>"📞 ℕ𝕠𝕞𝕖𝕣 𝕠𝕝𝕚𝕤𝕙"]],
    [['text'=>"🔐 𝕄𝕖𝕟𝕚𝕟𝕘 𝕙𝕚𝕤𝕠𝕓𝕚𝕞"],['text'=>"💰 ℍ𝕚𝕤𝕠𝕓𝕟𝕚 𝕥𝕠'𝕝𝕕𝕚𝕣𝕚𝕤𝕙"]],
    [['text'=>"🛒 𝔹𝕦𝕪𝕦𝕣𝕥𝕞𝕒 𝕩𝕠𝕝𝕒𝕥𝕚"],['text'=>"🚀 ℝ𝕖𝕗𝕖𝕣𝕒𝕝 𝕪𝕚ğ𝕚𝕤𝕙"]],
    [['text'=>"☎️ 𝔸𝕕𝕞𝕚𝕟𝕚𝕤𝕥𝕣𝕒𝕥𝕠𝕣"],['text'=>"🤝 ℍ𝕒𝕞𝕜𝕠𝕣𝕝𝕚𝕜 (𝔸ℙ𝕀)"]],
    [['text'=>"🗄️ Boshqaruv"]],
]]);

$resu    = mysqli_query($connect,"SELECT * FROM `settings`");
$setting = mysqli_fetch_assoc($resu);

if(in_array($cid,$admins) or in_array($chat_id,$admins)) $m=$menu_p;
else $m=$menu;

// ─── BOT O'CHIRILGANDA ────────────────────────────────────────────
if($botdel){
    if($userstatus=="kicked"){
        mysqli_query($connect,"UPDATE `users` SET `status` = 'deactive' WHERE `id` = '$botdel_id'");
    }
}

// ─── DEACTIVE FOYDALANUVCHI ───────────────────────────────────────
if(isset($update)){
    $result=mysqli_query($connect,"SELECT * FROM users WHERE id = $cid$chat_id");
    $rew=mysqli_fetch_assoc($result);
    if($rew['status']=="deactive") exit();
}

// ─── BOT MUZLATILGAN ──────────────────────────────────────────────
if($update){
    if(get("status.txt")=="frozen"){
        sms($cid.$chat_id,"🥶 Panel vaqtincha muzlatilgan",null);
    }
}

// ═════════════════════════════════════════════════════════════════
// ─── ADMIN BUYRUQLARI ─────────────────────────────────────────────
// ═════════════════════════════════════════════════════════════════

// ─── NOMER API BALANS ─────────────────────────────────────────────
if($text=="📞 Nomer API balans" and in_array($cid,$admins)){
    $url=file_get_contents("https://api.sms-activate.org/stubs/handler_api.php?api_key=$simkey&action=getBalance");
    $h=explode(":",$url)[1];
    sms($cid,"<b>📄 API ma'lumotlari:
➖➖➖➖➖➖➖➖➖➖➖
Ulangan sayt:</b>
<code>sms-activate.org</code>

<b>API kalit:</b>
<code>$simkey</code>

<b>API hisob:</b> $h ₽
➖➖➖➖➖➖➖➖➖➖➖",$panel);
    unlink("user/$cid.step");
    exit;
}

// ─── BOSHQARUV ────────────────────────────────────────────────────
if($text=="🗄️ Boshqaruv" and in_array($cid,$admins)){
    sms($cid,"🖥️ Boshqaruv paneli",$panel);
    unlink("user/$cid.step");
    exit;
}

// ─── STATISTIKA ───────────────────────────────────────────────────
if($text=="📊 Statistika" and in_array($cid,$admins)){
    $stat=0; $ac=0; $dc=0; $pc=0; $cc=0; $bc=0; $fc=0; $jc=0; $ppc=0; $cp=0;
    $res=mysqli_query($connect,"SELECT * FROM users");
    $stat=mysqli_num_rows($res);
    $resi=mysqli_query($connect,"SELECT * FROM orders");
    $stati=mysqli_num_rows($resi);
    $stati?$stati:$stati="0";
    while($hi=mysqli_fetch_assoc($resi)){
        if($hi['status']=="Pending")$pc++;
        elseif($hi['status']=="Completed")$cc++;
        elseif($hi['status']=="Canceled")$bc++;
        elseif($hi['status']=="Failed")$fc++;
        elseif($hi['status']=="In progress")$jc++;
        elseif($hi['status']=="Partial")$ppc++;
        elseif($hi['status']=="Processing")$cp++;
    }
    while($h=mysqli_fetch_assoc($res)){
        if($h['status']=="active")$ac++;
        elseif($h['status']=="deactive")$dc++;
    }
    $seco=0;
    $resit=mysqli_query($connect,"SELECT * FROM services");
    $seco=mysqli_num_rows($resit);
    sms($cid,"
<b>📊 Statistika</b>
• Jami foydalanuvchilar: $stat ta
• Aktiv foydalanuvchilar: $ac ta
• O'chirilgan foydalanuvchilar: $dc ta

<b>📊 Buyurtmalar</b>
• Jami buyurtmalar: $stati ta
• Bajarilgan buyurtmalar: $cc ta
• Kutilayotgan buyurtmalar: $pc ta
• Jarayondagi buyurtmalar: $jc ta
• Bekor qilingan buyurtmalar: $bc ta
• Muvaffaqiyatsiz buyurtmalar: $fc ta
• Qisman bajarilgan buyurtmalar: $ppc ta
• Qayta ishlangan buyurtmalar: $cp ta

<b>📊 Xizmatlar:</b>
• Barcha xizmatlar: $seco ta
",keyboard([
        [['text'=>"♻️ Buyurtmalar xolatini yangilash",'callback_data'=>"update=orders"]],
        [['text'=>"🏆 TOP 100 Balans",'callback_data'=>"preyting"],['text'=>"🏆 Top 100 Referal",'callback_data'=>"treyting"]],
    ]));
    unlink("user/$cid.step");
}

// ─── ASOSIY SOZLAMALAR ────────────────────────────────────────────
if($text=="⚙️ Asosiy sozlamalar" and in_array($cid,$admins)){
    sms($cid,$text,$panel2);
}

// ─── VALYUTA KURSI ───────────────────────────────────────────────
if($text=="💵 Kursni o'rnatish" and in_array($cid,$admins)){
    sms($cid,"👉 Kerakli valyutasi tanlang:",json_encode(['inline_keyboard'=>[
        [['text'=>"AQSH dollari ($)",'callback_data'=>"course=usd"]],
        [['text'=>"Rossiya rubli (₽)",'callback_data'=>"course=rub"]],
        [['text'=>"Hindston rupiysi (₹)",'callback_data'=>"course=inr"]],
        [['text'=>"Turkiya lirasi (₺)",'callback_data'=>"course=try"]],
    ]]));
}

if((stripos($data,"course=")!==false)){
    $val=explode("=",$data)[1];
    $VAL=get("set/".$val) ?: 0;
    del(); sms($chat_id,"
1 - ".strtoupper($val)." narxini kiriting:

♻️ Joriy narx: ".$VAL." so'm",$aort);
    put("user/$chat_id.step","course=$val");
}

if((mb_stripos($step,"course=")!==false and is_numeric($text))){
    $val=explode("=",$step)[1];
    put("set/".$val,"$text");
    sms($cid,"✅ 1 - ".strtoupper($val)." narxi $text so'mga o'zgardi",$panel);
    unlink("user/$cid.step");
}

// ─── FOIZ ─────────────────────────────────────────────────────────
if($text=="⚖️ Foizni o'rnatish" and in_array($cid,$admins)){
    $m2=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM percent WHERE id = 1"))['percent'];
    $m2?:0;
    sms($cid,"⭐ Bot xizmatlari uchun foizni kiriting\n\n♻️ Joriy foiz: $m2%",$aort);
    put("user/$cid.step","updFoiz");
}
if($step=="updFoiz"){
    if(is_numeric($text)){
        mysqli_query($connect,"UPDATE percent SET percent = '$text' WHERE id = 1");
        sms($cid,"✅ O'zgartirish muvaffaqiyatli bajarildi.",$panel);
    }
    put("user/$cid.step","");
}

// ─── XABAR YUBORISH ───────────────────────────────────────────────
if($text=="🔔 Xabar yuborish" and in_array($cid,$admins)){
    $result=mysqli_query($connect,"SELECT * FROM `send`");
    $row=mysqli_fetch_assoc($result);
    if(!$row){
        bot('sendMessage',['chat_id'=>$cid,'text'=>"<b>📤 Foydalanuvchilarga yuboriladigan xabarni botga yuboring!</b>",'parse_mode'=>'html','reply_markup'=>$aort]);
        put("user/$cid.step","send");
    }else{
        bot('sendMessage',['chat_id'=>$cid,'text'=>"<b>📑 Hozirda botda xabar yuborish jarayoni davom etmoqda.</b>",'parse_mode'=>'html','reply_markup'=>$panel]);
    }
}

if($step=="send" and in_array($cid,$admins)){
    $result=mysqli_query($connect,"SELECT * FROM users");
    $stat=mysqli_num_rows($result);
    $res=mysqli_query($connect,"SELECT * FROM users WHERE user_id = '$stat'");
    $row=mysqli_fetch_assoc($res);
    $user_id=$row['id'];
    $time1=date('H:i',strtotime('+1 minutes'));
    $time2=date('H:i',strtotime('+2 minutes'));
    $time3=date('H:i',strtotime('+3 minutes'));
    $time4=date('H:i',strtotime('+4 minutes'));
    $time5=date('H:i',strtotime('+5 minutes'));
    $tugma=json_encode($update->message->reply_markup);
    $reply_markup=base64_encode($tugma);
    mysqli_query($connect,"INSERT INTO `send` (`time1`,`time2`,`time3`,`time4`,`time5`,`start_id`,`stop_id`,`admin_id`,`message_id`,`reply_markup`,`step`) VALUES ('$time1','$time2','$time3','$time4','$time5','0','$user_id','$admin','$mid','$reply_markup','send')");
    bot('sendMessage',['chat_id'=>$admin,'text'=>"<b>📋 Saqlandi!\n📑 Xabar foydalanuvchilarga $time1 da yuborish boshlanadi!</b>",'parse_mode'=>'html','reply_markup'=>$panel]);
    unlink("user/$cid.step");
}

// ─── CRON YUBORISH ────────────────────────────────────────────────
$result2=mysqli_query($connect,"SELECT * FROM `send`");
$row2=mysqli_fetch_assoc($result2);
if($_GET['update']=="send"){
    $row1=$row2['time1']; $row2t=$row2['time2']; $row3=$row2['time3']; $row4=$row2['time4']; $row5=$row2['time5'];
    $start_id=$row2['start_id']; $stop_id=$row2['stop_id']; $admin_id=$row2['admin_id'];
    $mied=$row2['message_id']; $tugma=$row2['reply_markup'];
    $reply_markup=($tugma=="bnVsbA==")?"":(base64_decode($tugma));
    $limit=150;
    if($time==$row1 or $time==$row2t or $time==$row3 or $time==$row4 or $time==$row5){
        $sql="SELECT * FROM `users` LIMIT $start_id,$limit";
        $res=mysqli_query($connect,$sql);
        while($a=mysqli_fetch_assoc($res)){
            $id=$a['id'];
            bot('forwardMessage',['chat_id'=>$id,'from_chat_id'=>$admin_id,'message_id'=>$mied,'disable_web_page_preview'=>true,'reply_markup'=>$reply_markup]);
            if($id==$stop_id){
                bot('sendMessage',['chat_id'=>$admin_id,'text'=>"<b>✅ Xabar barcha foydalanuvchilarga yuborildi!</b>",'parse_mode'=>'html']);
                mysqli_query($connect,"DELETE FROM `send`"); exit;
            }
        }
        $t1=date('H:i',strtotime('+1 minutes')); $t2=date('H:i',strtotime('+2 minutes'));
        $t3=date('H:i',strtotime('+3 minutes')); $t4=date('H:i',strtotime('+4 minutes')); $t5=date('H:i',strtotime('+5 minutes'));
        mysqli_query($connect,"UPDATE `send` SET `time1`='$t1',`time2`='$t2',`time3`='$t3',`time4`='$t4',`time5`='$t5'");
        $get_id=$start_id+$limit;
        mysqli_query($connect,"UPDATE `send` SET `start_id`='$get_id'");
        bot('sendMessage',['chat_id'=>$admin_id,'text'=>"<b>✅ Yuborildi: $get_id</b>",'parse_mode'=>'html']);
    }
    echo json_encode(["status"=>true,"cron"=>"Sending message"]);
}

// ─── BUYURTMA HOLATI YANGILASH (CRON) ─────────────────────────────
if($_GET['update']=="status"){
    echo json_encode(["status"=>true,"cron"=>"Orders status"]);
    $mysql=mysqli_query($connect,"SELECT * FROM `orders`");
    while($mys=mysqli_fetch_assoc($mysql)){
        $prv=$mys['provider']; $order=$mys['api_order']; $uorder=$mys['order_id'];
        $mysa=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM `myorder` WHERE order_id=$uorder"));
        $adm=$mysa['user_id']; $retail=$mysa['retail'];
        if($mys['status']=="Canceled" or $mys['status']=="Completed") continue;
        $mprov=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM `providers` WHERE id = $prv"));
        $surl=$mprov['api_url']; $skey=$mprov['api_key'];
        $sav=date("Y.m.d H:i:s");
        $j=json_decode(get($surl."?key=".$skey."&action=status&order=$order"),1);
        $status=$j['status'];
        if($status){ mysqli_query($connect,"UPDATE orders SET status='$status' WHERE order_id=$uorder"); mysqli_query($connect,"UPDATE myorder SET status='$status', last_check='$sav' WHERE order_id=$uorder"); }
        $error=$j['error'];
        if(isset($error)){ mysqli_query($connect,"DELETE FROM myorder WHERE order_id = $uorder"); }
        elseif($status=="Completed"){ sms($adm,"✅ Sizning $uorder raqamli buyurtmangiz bajarildi",null); mysqli_query($connect,"DELETE FROM myorder WHERE order_id = $uorder"); }
        elseif($status=="Canceled"){
            sms($adm,"❌ Sizning $uorder raqamli buyurtmangiz bekor qilindi\n\n💳 Hisobingizga $retail so'm qaytarildi",null);
            $rew2=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE id = $adm"));
            $miqdor=$retail+$rew2['balance'];
            mysqli_query($connect,"UPDATE users SET balance=$miqdor WHERE id =$adm");
        }
    }
}

// ─── CRON SOZLAMASI ───────────────────────────────────────────────
if($text=="⏰ Cron sozlamasi" and in_array($cid,$admins)){
    sms($cid,"
📝 Quyidagi manzillarni cron qiling
<pre>https://".$_SERVER['SERVER_NAME']."".$_SERVER['SCRIPT_NAME']."?update=send</pre>
- Pochta xabari uchun cron (1 daqiqa)

<pre>https://".$_SERVER['SERVER_NAME']."".$_SERVER['SCRIPT_NAME']."?update=status</pre>
- Buyurtma xolati uchun cron (1 daqiqa)
",$panel);
}

// ─── BOT TEZLIGI ──────────────────────────────────────────────────
if($text=="🤖 Bot tezligi"){
    $start_time=round(microtime(true)*1000);
    bot('sendMessage',['chat_id'=>$cid,'text'=>"",'parse_mode'=>'html']);
    $end_time=round(microtime(true)*1000);
    $ping=$end_time-$start_time;
    $d=sms($cid,"<b>⏰ Kuting...</b>",null)->result->message_id;
    sleep(0.5); $s=edit($cid,$d,"<b>🤖 Bot</b>",null)->result->message_id;
    sleep(0.5); $e=edit($cid,$s,"<b>🤖 Bot tezligi</b>",null)->result->message_id;
    sleep(0.5); $se=edit($cid,$e,"<b>🤖 Bot tezligi:</b> $ping",null)->result->message_id;
    sleep(0.5); edit($cid,$se,"<b>🤖 Bot tezligi:</b> $ping m/s",null);
}

// ─── BOT HOLATI ───────────────────────────────────────────────────
if($text=="🤖 Bot holati"){
    if(in_array($cid,$admins)){
        $holat=file_get_contents("tizim/holat.txt");
        bot('SendMessage',['chat_id'=>$cid,'text'=>"<b>Hozirgi holat:</b> $holat",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[
            [['text'=>"✅",'callback_data'=>"holat-✅"],['text'=>"❌",'callback_data'=>"holat-❌"]],
            [['text'=>"Yopish",'callback_data'=>"yopish"]]
        ]])]);
        exit;
    }
}
if(mb_stripos($data,"holat-")!==false){
    $xolat=explode("-",$data)[1];
    file_put_contents("tizim/holat.txt",$xolat);
    bot('editMessageText',['chat_id'=>$cid2,'message_id'=>$mid2,'text'=>"<b>Hozirgi holat:</b> $xolat",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[
        [['text'=>"✅",'callback_data'=>"holat-✅"],['text'=>"❌",'callback_data'=>"holat-❌"]],
        [['text'=>"Yopish",'callback_data'=>"yopish"]]
    ]])]);
}

// ─── CHEGIRMALAR ──────────────────────────────────────────────────
if($text=="🛍 Chegirmalar" and in_array($cid,$admins)){
    sms($cid,"<b>🛍 Chegirmalar - bo'limi kerakli menuni tanlang:</b>",keyboard([
        [['text'=>"🛒 Chegirma qo'shish",'callback_data'=>"chegirma=add"]],
        [['text'=>"🗑️ Chegirmani o'chirish",'callback_data'=>"chegirma=dell"]],
    ]));
}
$mpercent=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM percent WHERE id = 1"))['percent'];
$mmax=$mpercent-1;
if($data=="chegirma=add" and in_array($chat_id,$admins)){
    for($i=1;$i<=$mmax;$i++) $k[]=['text'=>$i];
    $keys=array_chunk($k,6);
    $keys[]=[['text'=>"🗄️ Boshqaruv"]];
    $fgh=json_encode(['resize_keyboard'=>true,'keyboard'=>$keys]);
    sms($cid2,"➡️ Chegirma miqdorini kiriting:\n\n⚠️ Maksimal kiritish: $mmax%",$fgh);
    put("user/$cid2.step","chegirma1");
}
if($step=="chegirma1" and $text<=$mmax and is_numeric($text)==1){
    sms($cid,"💵 Chegirma narxini kiriting:",$aort);
    $upx=json_decode(get("set/chegirma"),1); $upx['count']=$text;
    file_put_contents("set/chegirma",json_encode($upx,JSON_PRETTY_PRINT));
    put("user/$cid.step","chegirma2");
}
if($step=="chegirma2" and is_numeric($text)==1){
    $maxd=31;
    for($i=1;$i<=$maxd;$i++) $k[]=['text'=>$i];
    $keys=array_chunk($k,7); $keys[]=[['text'=>"🗄️ Boshqaruv"]];
    $fgh=json_encode(['resize_keyboard'=>true,'keyboard'=>$keys]);
    sms($cid,"📅 Amal qilish muddatini kiriting:\n\n⚠️ Maksimal muddat: $maxd kun",$fgh);
    $upx=json_decode(get("set/chegirma"),1); $upx['price']=floor($text);
    file_put_contents("set/chegirma",json_encode($upx,JSON_PRETTY_PRINT));
    put("user/$cid.step","chegirma3");
}
if($step=="chegirma3" and $text<=31 and is_numeric($text)==1){
    sms($cid,"📋 Chegirma xaqida bir qancha malumotlar kiriting:",null);
    $upx=json_decode(get("set/chegirma"),1); $upx['expire']=floor($text);
    file_put_contents("set/chegirma",json_encode($upx,JSON_PRETTY_PRINT));
    put("user/$cid.step","chegirma4");
}
if($step=="chegirma4"){
    $upx=json_decode(get("set/chegirma"),1); $upx['about']=$text;
    file_put_contents("set/chegirma",json_encode($upx,JSON_PRETTY_PRINT));
    sms($cid,"
📋 Ma'lumotlarni o'qib chiqing:

⭐ Chegirma: <b>-".$upx['count']."%</b>
💵 Narxi: <b>".$upx['price']." so'm</b>
📅 Muddati: <b>".$upx['expire']." kun</b>

<i>".$upx['about']."</i>
",keyboard([
        [['text'=>"✅ Tasdiqlash",'callback_data'=>"addnewdiscount"]],
        [['text'=>"❌ O'chirish",'callback_data'=>"dabsds"]]
    ]));
    put("user/$cid.step","chegirma5");
}
if($data=="addnewdiscount" and in_array($chat_id,$admins)){
    bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"⏫ Serverga yuklanmoqda...",'show_alert'=>false]);
    del();
    $upx=json_decode(get("set/chegirma")); $upx->about=base64_encode($upx->about);
    if($connect->query("INSERT INTO chegirma(`price`,`count`,`expire`,`about`) VALUES ('$upx->price','$upx->count','$upx->expire','$upx->about')")===TRUE){
        sms($cid2,"✅ Malumotlarni saqlash jarayoni tugallandi.",$panel); unlink("user/$cid2.step");
    }else{ sms($cid2,"⚠️ Xatolik yuz berdi.\n\n".$connect->error."",null); }
}elseif($data=="dabsds"){ sms($cid2,"🗄️ Boshqaruv",$panel); unlink("user/$cid2.step"); del(); }

// ─── FOYDALANUVCHINI BOSHQARISH ───────────────────────────────────
if($text=="👤 Foydalanuvchini boshqarish"){
    if(in_array($cid,$admins)){
        bot('SendMessage',['chat_id'=>$cid,'text'=>"<b>Kerakli foydalanuvchining ID raqamini kiriting:</b>",'parse_mode'=>'html','reply_markup'=>$aort]);
        file_put_contents("user/$cid.step","iD");
    }
}
if($step=="iD"){
    if(in_array($cid,$admins)){
        $rew3=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE user_id = $text"));
        if($rew3){
            $idi=$rew3['id']; file_put_contents("user/us.id",$idi);
            $pul3=$rew3['balance']; $ban=$rew3['status'];
            $bans=($ban=="active")?"🔔 Banlash":"🔕 Bandan olish";
            bot('SendMessage',['chat_id'=>$cid,'text'=>"<b>Qidirilmoqda...</b>",'parse_mode'=>'html']);
            bot('editMessageText',['chat_id'=>$cid,'message_id'=>$mid+1,'text'=>"<b>Foydalanuvchi topildi!\n\nID:</b> <a href='tg://user?id=$idi'>$text</a>\n<b>Balans: $pul3 so'm</b>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[
                [['text'=>$bans,'callback_data'=>"ban"]],
                [['text'=>"➕ Pul qo'shish",'callback_data'=>"plus"],['text'=>"➖ Pul ayirish",'callback_data'=>"minus"]],
            ]])]);
            unlink("user/$cid.step");
        }else{
            bot('SendMessage',['chat_id'=>$cid,'text'=>"<b>Foydalanuvchi topilmadi.\n\nQayta urinib ko'ring:</b>",'parse_mode'=>'html']);
        }
    }
}
$saved=file_get_contents("user/us.id");
if($data=="plus"){ bot('sendMessage',['chat_id'=>$chat_id,'text'=>"<a href='tg://user?id=$saved'>$saved</a> <b>ning hisobiga qancha pul qo'shmoqchisiz?</b>",'parse_mode'=>"html",'reply_markup'=>$aort]); file_put_contents("user/$chat_id.step","plus"); }
if($step=="plus"){ if(in_array($cid,$admins)){ if(is_numeric($text)=="true"){ bot('sendMessage',['chat_id'=>$saved,'text'=>"<b>Adminlar tomonidan hisobingiz $text so'm to'ldirildi</b>",'parse_mode'=>"html",'reply_markup'=>$menu]); bot('sendMessage',['chat_id'=>$cid,'text'=>"<b>Foydalanuvchi hisobiga $text so'm qo'shildi!</b>",'parse_mode'=>"html",'reply_markup'=>$panel]); $rew4=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE id = $saved")); $miqdor=$text+$rew4['balance']; $p2=$text+$rew4['outing']; mysqli_query($connect,"UPDATE users SET balance=$miqdor, outing=$p2 WHERE id =$saved"); unlink("user/$cid.step"); }else{ bot('SendMessage',['chat_id'=>$cid,'text'=>"<b>Faqat raqamlardan foydalaning!</b>",'parse_mode'=>'html']); } } }
if($data=="minus"){ bot('sendMessage',['chat_id'=>$chat_id,'text'=>"<a href='tg://user?id=$saved'>$saved</a> <b>ning hisobidan qancha pul ayirmoqchisiz?</b>",'parse_mode'=>"html",'reply_markup'=>$aort]); file_put_contents("user/$chat_id.step","minus"); }
if($step=="minus"){ if(in_array($cid,$admins)){ if(is_numeric($text)=="true"){ bot('sendMessage',['chat_id'=>$saved,'text'=>"<b>Adminlar tomonidan hisobingizdan $text so'm olindi.</b>",'parse_mode'=>"html",'reply_markup'=>$menu]); bot('sendMessage',['chat_id'=>$cid,'text'=>"<b>Foydalanuvchi hisobidan $text so'm olindi!</b>",'parse_mode'=>"html",'reply_markup'=>$panel]); $rew5=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE id = $saved")); $miqdor=$rew5['balance']-$text; $p2=$rew5['outing']-$text; mysqli_query($connect,"UPDATE users SET balance=$miqdor, outing=$p2 WHERE id =$saved"); unlink("user/$cid.step"); }else{ bot('SendMessage',['chat_id'=>$cid,'text'=>"<b>Faqat raqamlardan foydalaning!</b>",'parse_mode'=>'html']); } } }
if($data=="ban"){ $rew6=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE id = $saved")); if(!in_array($saved,$admins)){ if($rew6['status']=="deactive"){ mysqli_query($connect,"UPDATE users SET status='active' WHERE id =$saved"); bot('sendMessage',['chat_id'=>$chat_id,'text'=>"<b>Foydalanuvchi ($saved) bandan olindi!</b>",'parse_mode'=>"html",'reply_markup'=>$panel]); }else{ mysqli_query($connect,"UPDATE users SET status='deactive' WHERE id =$saved"); bot('sendMessage',['chat_id'=>$chat_id,'text'=>"<b>Foydalanuvchi ($saved) banlandi!</b>",'parse_mode'=>"html",'reply_markup'=>$panel]); } }else{ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"Bloklash mumkin emas!",'show_alert'=>true]); } }

// ─── MAJBURIY OBUNALAR ────────────────────────────────────────────
if($text=="📎 Majburiy obunalar" and in_array($cid,$admins)){
    sms($cid,$text,json_encode(['inline_keyboard'=>[
        [['text'=>"➕ Qo'shish",'callback_data'=>"kanal=add"],['text'=>"🆕️ Promokod uchun",'callback_data'=>"promo"]],
        [['text'=>"*️⃣ Ro'yxat",'callback_data'=>"kanal=list"],['text'=>"🗑️ O'chirish",'callback_data'=>"kanal=dl"]],
    ]]));
}
if((stripos($data,"kanal=")!==false)){
    $rp=explode("=",$data)[1];
    if($rp=="list"){
        $ops=get("set/channel");
        if(empty($ops)){ sms($chat_id,"🤷‍♂️ Xechqanday kanal topilmadi.",null); }
        else{ $s=explode("\n",$ops); for($i=0;$i<=count($s)-1;$i++) $k[]=['text'=>$s[$i],'url'=>"t.me/".str_replace("@","",$s[$i])]; $keyboard2=array_chunk($k,2); sms($chat_id,"👉 Barcha kanallar:",json_encode(['inline_keyboard'=>$keyboard2])); }
    }elseif($rp=="dl"){
        $ops=get("set/channel");
        if(empty($ops)){ sms($chat_id,"🤷‍♂️ Xechqanday kanal topilmadi.",null); }
        else{ $s=explode("\n",$ops); for($i=0;$i<=count($s)-1;$i++) $k[]=['text'=>$s[$i],'callback_data'=>"kanal=del".$s[$i]]; $keyboard2=array_chunk($k,2); sms($chat_id,"🗑️ O'chiriladigan kanalni tanlang:",json_encode(['inline_keyboard'=>$keyboard2])); }
    }elseif(mb_stripos($rp,"del@")!==false){
        $d=explode("@",$rp)[1]; $ops=get("set/channel"); $soni=explode("\n",$ops);
        if(count($soni)==1) unlink("set/channel");
        else{ $ss="@".$d; $ops=str_replace("\n".$ss."",$ss,""); $ops=str_replace("\n$ss",",$ss."",""$ops); put("set/channel",$ops); }
        del(); sms($chat_id,"✅ O'chirildi",null);
    }elseif($rp=="add"){
        del(); sms($chat_id,"♻️ Kanal userini kiriting\n\nNamuna: @kanal",$aort);
        put("user/$chat_id.step","kanal_add");
    }
}
if($step=="kanal_add"){ if(mb_stripos($text,"@")!==false){ $kanal=get("set/channel"); sms($cid,"✅ Saqlandi!",$panel); if($kanal==null) file_put_contents("set/channel",$text); else file_put_contents("set/channel","$kanal\n$text"); unlink("user/$chat_id.step"); } }

// ─── API SOZLAMALARI ──────────────────────────────────────────────
if($text=="🔑 API Sozlamalari"){ if(in_array($cid,$admins)){ bot('SendMessage',['chat_id'=>$cid,'text'=>"Quyidagi bo'limlardan birini tanlang:",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"➕ API qo'shish",'callback_data'=>"api"]], [['text'=>"💵 Balansni ko'rish",'callback_data'=>"balans"]], [['text'=>"🗑️ O'chirish",'callback_data'=>"deleteapi"]], [['text'=>"📝 Taxrirlash",'callback_data'=>"apio=taxrirlash"]], ]])]); exit; } }
if($data=="api"){ bot('deleteMessage',['chat_id'=>$chat_id,'message_id'=>$message_id]); bot('SendMessage',['chat_id'=>$chat_id,'text'=>"<b>API manzilini yuboring:\n\nNamuna:</b> <pre>https://example.com/api/v2</pre>",'parse_mode'=>'html','reply_markup'=>$aort]); file_put_contents("user/$chat_id.step","api_url"); exit; }
if($step=="api_url"){ if(in_array($cid,$admins)){ if(mb_stripos($text,"https://")!==false and isset($text)){ file_put_contents("set/api_url",$text); bot('SendMessage',['chat_id'=>$cid,'text'=>"$text <b>qabul qilindi!\n\nEndi esa ushbu saytdan olingan API_KEY'ni kiriting:</b>",'disable_web_page_preview'=>true,'parse_mode'=>'html']); file_put_contents("user/$cid.step","api"); exit; }else{ bot('SendMessage',['chat_id'=>$cid,'text'=>"<b>API manzilini to'g'ri yuboring</b>",'parse_mode'=>'html']); exit; } } }
if($step=="api"){ if(in_array($cid,$admins) and isset($text)){ $balans=json_decode(file_get_contents(get("set/api_url")."?key=$text&action=balance"),true); if(isset($balans['error'])){ $admsg="⚠️ API kalit mavjud emas"; }else{ $admsg="<b>💵 API balansi:</b> ".$balans['balance']." ".$balans['currency'].""; $api_url=get("set/api_url"); mysqli_query($connect,"INSERT INTO providers(`api_url`,`api_key`) VALUES ('$api_url','$text')"); } bot('SendMessage',['chat_id'=>$cid,'text'=>"<b>$admsg</b>",'parse_mode'=>'html','reply_markup'=>$panel2]); unlink("user/$cid.step"); } }
if($data=="balans"){ $pr=0; $prs=""; $a=mysqli_query($connect,"SELECT * FROM providers"); $c=mysqli_num_rows($a); while($s=mysqli_fetch_assoc($a)){ $pr++; $prtxt=str_replace(["/api/adapter/default/index","/api/v1","/api/v2","https://"],["","","",""],$s['api_url']); $sa=json_decode(api_query($s['api_url']."?key=".$s['api_key']."&action=balance")); $prs.="<b>".$pr."</b>: $prtxt - ".$sa->balance." ".$sa->currency." \n"; $k[]=['text'=>$pr,'url'=>$s['api_url']."?key=".$s['api_key']."&action=balance"]; } $keyboard2=array_chunk($k,3); $keyboard2[]=[['text'=>"Orqaga",'callback_data'=>"api1"]]; $kb=json_encode(['inline_keyboard'=>$keyboard2]); if(!$c){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"⚠️ Provayderlar topilmadi!",'show_alert'=>true]); }else{ bot('editMessageText',['chat_id'=>$chat_id,'message_id'=>$message_id,'text'=>"Provayderni tanlang:\n\n$prs",'parse_mode'=>"HTML",'reply_markup'=>$kb]); } }
if($data=="deleteapi"){ $pr=0; $a=mysqli_query($connect,"SELECT * FROM providers"); $c=mysqli_num_rows($a); while($s=mysqli_fetch_assoc($a)){ $pr++; $prtxt=str_replace(["/api/adapter/default/index","/api/v1","/api/v2","https://"],["","","",""],$s['api_url']); $prs.="$pr: <b>$prtxt\n</b>"; $k[]=['text'=>$pr,'callback_data'=>"apidel=".$s['id']]; } $keyboard2=array_chunk($k,3); $keyboard2[]=[['text'=>"Orqaga",'callback_data'=>"api1"]]; $kb=json_encode([inline_keyboard=>$keyboard2]); if(!$c){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"⚠️ Provayderlar topilmadi!",'show_alert'=>true]); }else{ bot('editMessageText',['chat_id'=>$chat_id,'message_id'=>$message_id,'text'=>"Provayderni tanlang:\n\n$prs",'parse_mode'=>"HTML",'reply_markup'=>$kb]); exit; } }
if((stripos($data,"apidel=")!==false)){ $res=explode("=",$data)[1]; del(); mysqli_query($connect,"DELETE FROM providers WHERE id = $res"); mysqli_query($connect,"DELETE FROM services WHERE api_service = $res"); sms($cid2,"🗑️ Provayderni o'chirish yakunlandi.",null); }
if($data=="api1"){ bot('deleteMessage',['chat_id'=>$chat_id,'message_id'=>$message_id]); bot('SendMessage',['chat_id'=>$chat_id,'text'=>"Quyidagi bo'limlardan birini tanlang:",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"➕ API qo'shish",'callback_data'=>"api"]], [['text'=>"💵 Balansni ko'rish",'callback_data'=>"balans"]], [['text'=>"🗑️ O'chirish",'callback_data'=>"deleteapi"]], [['text'=>"📝 Taxrirlash",'callback_data'=>"apio=taxrirlash"]], ]])]); exit; }

// ─── BUYURTMALARNI SOZLASH ────────────────────────────────────────
if($text=="🛍 Buyurtmalarni sozlash" and in_array($cid,$admins)){ bot('sendMessage',['chat_id'=>$cid,'text'=>"<b>Quyidagilardan birini tanlang:</b>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"📂 Bo'limlarni sozlash",'callback_data'=>"bolim"]], [['text'=>"📂 Ichki bo'limlarni sozlash",'callback_data'=>"ichki"]], [['text'=>"🛍 Xizmatlarni sozlash",'callback_data'=>"xizmat"]] ]])]); }
if($data=="xsetting"){ del(); bot('sendMessage',['chat_id'=>$chat_id,'text'=>"<b>Quyidagilardan birini tanlang:</b>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"📂 Bo'limlarni sozlash",'callback_data'=>"bolim"]], [['text'=>"📂 Ichki bo'limlarni sozlash",'callback_data'=>"ichki"]], [['text'=>"🛍 Xizmatlarni sozlash",'callback_data'=>"xizmat"]] ]])]); }

// ─── BOLIM ────────────────────────────────────────────────────────
if($data=="bolim"){ bot('editMessageText',['chat_id'=>$chat_id,'message_id'=>$message_id,'text'=>"<b>Quyidagilardan birini tanlang:</b>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"Yangi bo'lim qo'shish",'callback_data'=>"newFol"]], [['text'=>"Tahrirlash",'callback_data'=>"editFol"]], [['text'=>"O'chirish",'callback_data'=>"delFol"]], [['text'=>"Orqaga",'callback_data'=>"xsetting"]], ]])]); }
if($data=="newFol"){ bot('deleteMessage',['chat_id'=>$chat_id,'message_id'=>$message_id]); bot('sendMessage',['chat_id'=>$chat_id,'text'=>"<b>Yangi bo'lim nomini yuboring:</b>",'parse_mode'=>'html','reply_markup'=>$aort]); file_put_contents("user/$chat_id.step","newFol"); }
if($step=="newFol"){ $text2=enc("encode",$text); mysqli_query($connect,"INSERT INTO categorys(category_name,category_status) VALUES('$text2','ON');"); bot('SendMessage',['chat_id'=>$cid,'text'=>"Bo'lim qo'shildi!",'parse_mode'=>'html','reply_markup'=>$panel2]); unlink("user/$cid.step"); }
if($data=="delFol"){ $a=mysqli_query($connect,"SELECT * FROM categorys"); $c=mysqli_num_rows($a); while($s=mysqli_fetch_assoc($a)) $k[]=['text'=>enc("decode",$s['category_name']),'callback_data'=>"delFols=".$s['category_id']]; $keyboard2=array_chunk($k,1); $kb=json_encode(['inline_keyboard'=>$keyboard2]); if(!$c){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"⚠️ Bo'limlar topilmadi!",'show_alert'=>true]); }else{ edit($chat_id,$message_id,"👉 O'zingizga kerakli tarmoqni tanlang:",$kb); } }
if(mb_stripos($data,"delFols=")!==false){ $ex=explode("=",$data)[1]; $sd7=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM categorys WHERE category_id = $ex")); $cd=$sd7['category_id']; $qd=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM cates WHERE category_id = $ex")); $sa=$qd['cate_id']; mysqli_query($connect,"DELETE FROM services WHERE category_id=$sa"); mysqli_query($connect,"DELETE FROM cates WHERE category_id = $cd"); mysqli_query($connect,"DELETE FROM categorys WHERE category_id='$ex'"); bot('deleteMessage',['chat_id'=>$chat_id,'message_id'=>$message_id]); bot('sendMessage',['chat_id'=>$chat_id,'text'=>"Bo'lim olib tashlandi!",'parse_mode'=>'html','reply_markup'=>$panel2]); }

// ─── XIZMAT ───────────────────────────────────────────────────────
if($data=="xizmat"){ bot('editMessageText',['chat_id'=>$chat_id,'message_id'=>$message_id,'text'=>"<b>Quyidagilardan birini tanlang:</b>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"Yangi xizmat qo'shish",'callback_data'=>"newXiz"]], [['text'=>"Xizmatlarni yuklab olish",'callback_data'=>"uplXiz"]], [['text'=>"Tahrirlash",'callback_data'=>"editXiz"]], [['text'=>"O'chirish",'callback_data'=>"delXiz"]], [['text'=>"Orqaga",'callback_data'=>"xsetting"]], ]])]); }

// ─── FOYDALANUVCHI MENYUSI ────────────────────────────────────────

// /start
if($text=="/start" and joinchat($cid)==1){
    $rew7=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE id = $cid"));
    $start=str_replace(["{name}","{balance}","{time}"],["$name","".$rew7['balance']."","$time"],enc("decode",$setting['start']));
    sms($cid,$start,$m);
}

// Orqaga
if($text=="➡️ Orqaga" and joinchat($cid)==1){
    sms($cid,"🖥️ Asosiy menyudasiz",$m);
    unlink("user/$cid.step"); exit();
}

// Mening hisobim
if($text=="🔐 𝕄𝕖𝕟𝕚𝕟𝕘 𝕙𝕚𝕤𝕠𝕓𝕚𝕞" and joinchat($cid)==1){
    $rew8=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE id = $cid"));
    $orders8=mysqli_num_rows(mysqli_query($connect,"SELECT * FROM `myorder` WHERE `user_id` = $cid"));
    sms($cid,"<b>👤 Sizning ID raqamingiz: $cid

<b>♻️ Holatiingiz:</b> ".$rew8['status']."
💵 Balansingiz:  ".$rew8['balance']."  soʻm
📊 Buyurtmalaringiz: $orders8 ta

💰 Kiritilgan summa:  ".$rew8['outing']." so'm
</b>",json_encode([
        inline_keyboard=>[
            [['text'=>"💰 ℍ𝕚𝕤𝕠𝕓𝕟𝕚 𝕥𝕠'𝕝𝕕𝕚𝕣𝕚𝕤𝕙",'callback_data'=>"menu=tolov"],['text'=>"🚀 ℝ𝕖𝕗𝕖𝕣𝕒𝕝 𝕪𝕚ğ𝕚𝕤𝕙",'callback_data'=>"pul_ishla"]],
            [['text'=>"🎟 Promokod",'callback_data'=>"kodpromo"],['text'=>"⭐️Premium",'callback_data'=>"preimium"]],
        ]
    ]));
}

// Hisobni to'ldirish menyu
if((stripos($data,"menu=")!==false and joinchat($chat_id)==1)){
    $res9=explode("=",$data)[1];
    if($res9=="tolov"){
        $ops=get("set/payments.txt"); $s=explode("\n",$ops); $soni=substr_count($ops,"\n");
        for($i=1;$i<=$soni;$i++) $k[]=['text'=>$s[$i],'callback_data'=>"payBot=".$s[$i]];
        $keyboard2=array_chunk($k,2);
        $keyboard2[]=[['text'=>"🅿️ PAYME AVTO",'callback_data'=>"paymeuz"]];
        $kb=json_encode(['inline_keyboard'=>$keyboard2]);
        edit($chat_id,$message_id,"<b>🔰 Quyidagi to'lov tizimlardan birini tanlang:\n\n👤 ID raqam:</b><code> $chat_id </code>",$kb);
    }
}

// To'lov tizimi tanlandi
if((stripos($data,"payBot=")!==false)){
    $h=explode("=",$data)[1];
    $card=get("set/pay/$h/wallet.txt"); $info=get("set/pay/$h/addition.txt");
    edit($cid2,$mid2,"
🧾 <b>To'lov tizimi: $h

💳 Hamyon: <code>$card</code>
📑 Izoh: <code>$cid2</code>

🔹 Minimal:</b> 2,000 so'm
🔹 <b>Maksimal:</b> 1,000,000 so'm

<b>$info</b>
",json_encode(['inline_keyboard'=>[
        [['text'=>"✅ To'lov qildim",'callback_data'=>"payed=$h"]],
        [['text'=>"↔️ Orqaga",'callback_data'=>"menu=tolov"]],
    ]]));
}

if(mb_stripos($data,"payed=")!==false){ $h=explode("=",$data)[1]; sms($chat_id,"🧾 <b>To'lov miqdorini kiriting:\n\n🔹 Minimal: 2,000 so'm\n🔹 Maksimal: 1,000,000 so'm</b>",$ort); put("user/$chat_id.step","tolovqldm=$h"); }
if(mb_stripos($step,"tolovqldm=")!==false){ $h=explode("=",$step)[1]; if(is_numeric($text)==true){ if(($text>=2000) and ("1000000">=$text)){ sms($cid,"📑 <b>To'lov uchun chek rasmini yuboring:</b>",$ort); file_put_contents("user/$cid.step","payed=$h=$text"); }else{ sms($cid,"⛔ <b>Qaytadan kiriting:\n\n🔹 Minimal: 2,000\n🔹 Maksimal: 1,000,000 so'm</b>",$ort); } }else{ sms($cid,"<b>⛔ Faqat raqamlardan foydalaning:</b>",$ort); } }
if(mb_stripos($step,"payed=")!==false){ $name9=bot('getchat',['chat_id'=>$cid])->result->first_name; unlink("user/$cid.step"); $ex=explode("=",$step); $h=$ex[1]; $miqdor9=$ex[2]; if($message->photo){ sms($cid,"<b>✅ To'lovingiz administratorga yuborildi!\n\n@$bot - bilan qoling</b>",$m); $ax=bot('CopyMessage',['chat_id'=>$admin,'message_id'=>$mid,'from_chat_id'=>$cid])->result->message_id; bot('sendMessage',['chat_id'=>$admin,'reply_to_message_id'=>$ax,'parse_mode'=>"html",'text'=>"<b>\n📑 #chek | To'lov uchun chek\n\n💳 To'lov tizimi: $h\n🔢 To'lov miqdori: $miqdor9 so'm</b>",'reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"✅ Tasdiqlash",'callback_data'=>"pdone=$cid=$h=$miqdor9"],['text'=>"⛔ Bekor qilish",'callback_data'=>"notpay=$cid=$miqdor9"]], [['text'=>$name9,'url'=>"tg://user?id=$cid"]], ]])]); }else{ sms($cid,"<b>⛔ Faqat rasm (screenshot) qabul qilinadi!</b>",$m); } }
if(mb_stripos($data,"pdone=")!==false){ if($callfrid==$admin or $callfrid==$admin2){ $ex=explode("=",$data); $id=$ex[1]; $tizim=$ex[2]; $miqdor9=$ex[3]; sms($id,"<b>✅ So'rovingiz tasdiqlandi va hisobingizga $miqdor9 so'm qo'shildi</b>",null); bot('editMessageText',['chat_id'=>$chat_id,'parse_mode'=>"html",'message_id'=>$message_id,'text'=>"💵 <b>Foydalanuvchi ($id) hisobi $miqdor9 so'mga to'ldirildi. || #done</b>"]); $rew9=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE id = $id")); $put=$miqdor9+$rew9['balance']; $p2=$miqdor9+$rew9['outing']; mysqli_query($connect,"UPDATE users SET balance=$put, outing=$p2 WHERE id = $id"); } }
if(mb_stripos($data,"notpay=")!==false){ if($callfrid==$admin or $callfrid==$admin2){ $ex=explode("=",$data); $use=$ex[1]; $miqdor9=$ex[2]; bot('editMessageText',['chat_id'=>$chat_id,'parse_mode'=>"html",'message_id'=>$message_id,'text'=>"⛔ <b>Foydalanuvchi ($use) hisobini $miqdor9 so'mga to'ldirish uchun so'rovi bekor qilindi! || #canceled</b>"]); sms($use,"<b>⛔ Hisobingizni $miqdor9 so'mga to'ldirish uchun so'rovingiz bekor qilindi!</b>",null); } }

// Referal
if($text=="🚀 ℝ𝕖𝕗𝕖𝕣𝕒𝕝 𝕪𝕚ğ𝕚𝕤𝕙" and joinchat($cid)==1){
    $result=mysqli_query($connect,"SELECT * FROM users WHERE id = $cid");
    $row=mysqli_fetch_assoc($result); $myid=$row['user_id'];
    sms($cid,"
Sizning referal havolangiz:

https://t.me/$bot?start=user$myid

Sizga har bir taklif qilgan referalingiz uchun ".enc("decode",$setting['referal'])." so'm beriladi.

👤ID raqam: $myid",json_encode([
        inline_keyboard=>[
            [['text'=>"💎 Konkurs (🏆 TOP 10)",'callback_data'=>"konkurs"]],
        ]
    ]));
}
if($data=="konkurs" and joinchat($chat_id)==1){ edit($cid2,$mid2,referal(10),null); }

// /start user referal
if(mb_stripos($text,"/start user")!==false){
    $id=str_replace("/start user","",$text);
    $refid=mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM users WHERE user_id = $id"))['id'];
    $res2=mysqli_query($connect,"SELECT*FROM users WHERE id=$cid");
    while($a=mysqli_fetch_assoc($res2)) $flid=$a['id'];
    if(strlen($refid)>0 and $refid>0){
        if($refid==$cid){ bot('SendMessage',['chat_id'=>$cid,'text'=>"⚠️ Siz o'zingizga referal bo'lishingiz mumkin emas",'parse_mode'=>'html','reply_markup'=>$m]); }
        else{
            if(mb_stripos($flid,"$cid")!==false){ bot('SendMessage',['chat_id'=>$cid,'text'=>"⚠️ Siz bizning botimizda allaqachon mavjudsiz.",'parse_mode'=>'html','reply_markup'=>$m]); }
            else{
                if(joinchat($cid)==1){ $pul10=mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM users WHERE id=$refid"))['balance']; $a10=$pul10+enc("decode",$setting['referal']); mysqli_query($connect,"UPDATE users SET balance = $a10 WHERE id = $refid"); $textref="📳 <b>Sizda yangi</b> <a href='tg://user?id=$cid'>taklif</a> <b>mavjud!</b>\n\nHisobingizga ".enc("decode",$setting['referal'])." so'm qo'shildi!"; $p10=get("user/$refid.users"); put("user/$refid.users",$p10+1); }
                else{ file_put_contents("user/$cid.id",$refid); $textref="📳 <b>Sizda yangi</b> <a href='tg://user?id=$cid'>taklif</a> <b>mavjud!</b>"; }
                bot('sendMessage',['chat_id'=>$cid,'text'=>"🖥 Asosiy menyudasiz",'parse_mode'=>'html','reply_markup'=>$m]);
                bot('SendMessage',['chat_id'=>$refid,'text'=>$textref,'parse_mode'=>'html']);
            }
        }
    }
}

// result - kanal tekshiruvi
if($data=="result" and joinchat($chat_id)==1){
    if(joinchat($chat_id)==1){
        $usid=get("user/$chat_id.id");
        $pul11=mysqli_fetch_assoc(mysqli_query($connect,"SELECT*FROM users WHERE id=$usid"))['balance'];
        $a11=$pul11+enc("decode",$setting['referal']);
        mysqli_query($connect,"UPDATE users SET balance = $a11 WHERE id = $usid");
        $text11="<a href='tg://user?id=$chat_id'>✅ Foydalanuvchi</a> <b> botimizdan foydalanib boshladi!</b>\n\nHisobingizga ".enc("decode",$setting['referal'])." so'm qo'shildi!";
        sms($usid,"$text11",$m);
        $p11=get("user/$usid.users"); put("user/$usid.users",$p11+1);
        unlink("user/$chat_id.id");
    }
    del(); sms($chat_id,"🖥️ Asosiy menyudasiz",$m);
}

// Administratorga murojaat
if($text=="☎️ 𝔸𝕕𝕞𝕚𝕟𝕚𝕤𝕥𝕣𝕒𝕥𝕠𝕣" and joinchat($cid)==1){ sms($cid,"\n⭐ Bizga savollaringiz bormi?\n\n📑 Murojaat matnini yozib yuboring.\n",$ort); put("user/$cid.step","murojaat"); }
if($step=="murojaat"){ sms($cid,"✅ Murojaatingiz qabul qilindi",$m); bot('copyMessage',[chat_id=>$admin,from_chat_id=>$cid,'message_id'=>$mid,'reply_markup'=>json_encode([inline_keyboard=>[ [['text'=>"👁️ Ko'rish",url=>"tg://user?id=$cid"]], [['text'=>"📑 Javob yozish",'callback_data'=>"javob=$cid"]], ]])]); put("user/$cid.step",""); }
if((stripos($data,"javob=")!==false)){ $ida=explode("=",$data)[1]; sms($admin,"$ida Foydalanuvchiga yuboriladigan xabaringizni kiriting.",$ort); put("user/$cid2.step","ticket=$ida"); }
if((mb_stripos($step,"ticket=")!==false) and in_array($cid,$admins)){ $ida=explode("=",$step)[1]; $if=bot('copyMessage',[chat_id=>$ida,from_chat_id=>$admin,'message_id'=>$mid]); if($if->ok==1) sms($cid,"✅ Xabar yuborildi",$panel); else sms($cid,"❌ Xabar yuborilmadi",$panel); unlink("user/$cid.step"); }

// Hamkorlik API
if($text=="🤝 ℍ𝕒𝕞𝕜𝕠𝕣𝕝𝕚𝕜 (𝔸ℙ𝕀)"){
    $result=mysqli_query($connect,"SELECT * FROM `users` WHERE id = '$cid'"); $rew12=mysqli_fetch_assoc($result);
    sms($cid,"
<b>⭐ Sizning API kalitingiz:
<code>".$rew12['api_key']."</code>

💵 API hisobi:
<b>".$rew12['balance']."</b> so'm
</b>",keyboard([
        [['text'=>"📝 Qo'llanma",'callback_data'=>"apidetail=qoll"]],
        [['text'=>"🔄 APIni yangilash",'callback_data'=>"apidetail=newkey"]],
    ]));
}
if((stripos($data,"apidetail=")!==false)){ $res12=explode("=",$data)[1]; if($res12=="newkey"){ $newkey=md5(uniqid()); mysqli_query($connect,"UPDATE users SET api_key = '$newkey' WHERE id = '$chat_id'"); $result=mysqli_query($connect,"SELECT * FROM `users` WHERE id = '$chat_id'"); $rew12=mysqli_fetch_assoc($result); bot('editMessageText',['chat_id'=>$chat_id,'parse_mode'=>"html",'message_id'=>$message_id,'text'=>"<b>\n✅ API kalit yangilandi.\n\n<code>".$rew12['api_key']."</code>\n\n💵 API hisobi:\n<b>".$rew12['balance']."</b> so'm\n</b>",'reply_markup'=>keyboard([[['text'=>"📝 Qo'llanma",'callback_data'=>"apidetail=qoll"]],[['text'=>"🔄 APIni yangilash",'callback_data'=>"apidetail=newkey"]]]) ]); } }

// Buyurtma berish
if($text=="🛍 𝔹𝕦𝕪𝕦𝕣𝕥𝕞𝕒 𝕓𝕖𝕣𝕚𝕤𝕙" and joinchat($cid)==1){
    bot('sendChatAction',['chat_id'=>$cid,'action'=>"typing"]);
    $a=mysqli_query($connect,"SELECT * FROM `categorys`"); $c=mysqli_num_rows($a);
    while($s=mysqli_fetch_assoc($a)) $k[]=['text'=>"".enc("decode",$s['category_name']),'callback_data'=>"tanla1=".$s['category_id']];
    $keyboard2=array_chunk($k,1);
    $keyboard2[]=[['text'=>"🎟️ Donat Xizmati",'callback_data'=>"servis"]];
    $keyboard2[]=[['text'=>"🔥 Eng yaxshi xizmatlar ⚡️",'url'=>"https://".$_SERVER['HTTP_HOST']."/services"]];
    $kb=json_encode(['inline_keyboard'=>$keyboard2]);
    if($c) sms($cid,"✅ Bizning xizmatlarimizni tanlaganingizdan xursandmiz!\n👇 Quydagi Ijtimoiy tarmoqlardan birini tanlang.",$kb);
    else sms($cid,"⚠️ Tarmoqlar topilmadi.",null);
}

if($data=="absd" and joinchat($chat_id)==1){ $a=mysqli_query($connect,"SELECT * FROM categorys"); $c=mysqli_num_rows($a); while($s=mysqli_fetch_assoc($a)) $k[]=['text'=>enc("decode",$s['category_name']),'callback_data'=>"tanla1=".$s['category_id']]; if(!$c){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"⚠️ Tarmoqlar topilmadi!",'show_alert'=>true]); }else{ $keyboard2=array_chunk($k,1); $keyboard2[]=[['text'=>"🎟️ Donat Xizmati",'callback_data'=>"servis"]]; $kb=json_encode(['inline_keyboard'=>$keyboard2]); edit($chat_id,$mid2,"✅ Bizning xizmatlarimizni tanlaganingizdan xursandmiz!\n👇 Quydagi Ijtimoiy tarmoqlardan birini tanlang.",$kb); exit; } }

if((mb_stripos($data,"tanla1=")!==false and joinchat($chat_id)==1)){ $n=explode("=",$data)[1]; $adds=json_decode(get("set/sub.json"),1); $adds['cate_id']=$n; put("set/sub.json",json_encode($adds)); $new_arr=[]; $k=[]; $a=mysqli_query($connect,"SELECT * FROM cates WHERE category_id = $n"); $c=mysqli_num_rows($a); while($s=mysqli_fetch_assoc($a)){ if(!in_array(enc("decode",$s['name']),$new_arr)){ $new_arr[]=enc("decode",$s['name']); $k[]=['text'=>"".enc("decode",$s['name']),'callback_data'=>"tanla2=".$s['cate_id']]; } } $keyboard2=array_chunk($k,1); $keyboard2[]=[['text'=>"⏪ Orqaga",'callback_data'=>"absd"]]; $kb=json_encode(['inline_keyboard'=>$keyboard2]); if(!$c){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"⚠️ Ushbu tarmq uchun xizmat turlari topilmadi!",'show_alert'=>true]); }else{ edit($chat_id,$message_id,"⬇️ Kerakli xizmat turini tanlang:",$kb); exit; } }

if(mb_stripos($data,"tanla2=")!==false and joinchat($chat_id)==1){ $n=explode("=",$data)[1]; $as=0; $a=mysqli_query($connect,"SELECT * FROM services WHERE category_id = '$n' AND service_status = 'on'"); $c=mysqli_num_rows($a); while($s=mysqli_fetch_assoc($a)){ $as++; $narx=$s['service_price']; $k[]=['text'=>"".base64_decode($s['service_name'])." $narx - so'm",'callback_data'=>"ordered=".$s['service_id']."=".$n]; } $keyboard2=array_chunk($k,1); $adds=json_decode(get("set/sub.json"),1); $keyboard2[]=[['text'=>"⏪ Orqaga",'callback_data'=>"tanla1=".$adds['cate_id']]]; $kb=json_encode(['inline_keyboard'=>$keyboard2]); if(!$c){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"⚠️ Ushbu bo'lim uchun xizmatlar topilmadi!",'show_alert'=>true]); }else{ edit($chat_id,$message_id,"⬇️ O'zingizga kerakli xizmatni tanlang:",$kb); exit; } }

// Donat
if($data=="servis"){ bot('sendChatAction',['chat_id'=>$cid,'action'=>"typing"]); bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); bot('SendMessage',['chat_id'=>$cid2,'text'=>"<b>✅ Bizning xizmatlarimizni tanlaganingizdan xursandmiz!\n👇 Quyidagi o'yinlardan birini tanlang:</b>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"🔵 PUBG UC",'callback_data'=>"ucpubg"],['text'=>"🔴 FREE FIRE ALMAZ",'callback_data'=>"fire"]] ]])]); exit(); }
if($data=="ucpubg"){ bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); bot('SendMessage',['chat_id'=>$cid2,'text'=>"<b>🔵 PUBG UC bo'limiga hush kelibsiz!</b>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"🔵 60 - $uc60 $valyuta",'callback_data'=>"xizm-60uc-PUBGMOBILE-UC"]],[['text'=>"🔵120 - $uc120 $valyuta",'callback_data'=>"xizm-120uc-PUBGMOBILE-UC"]],[['text'=>"🔵 180 - $uc180 $valyuta",'callback_data'=>"xizm-180uc-PUBGMOBILE-UC"]],[['text'=>"🔵 325 - $uc325 $valyuta",'callback_data'=>"xizm-325uc-PUBGMOBILE-UC"]],[['text'=>"🔵 385 - $uc385 $valyuta",'callback_data'=>"xizm-385uc-PUBGMOBILE-UC"]],[['text'=>"🔵 660 - $uc660 $valyuta",'callback_data'=>"xizm-660uc-PUBGMOBILE-UC"]],[['text'=>"🔵 720 - $uc720 $valyuta",'callback_data'=>"xizm-720uc-PUBGMOBILE-UC"]],[['text'=>"🔵 985 - $uc985 $valyuta",'callback_data'=>"xizm-985uc-PUBGMOBILE-UC"]],[['text'=>"🔵 1320 = $uc1320 $valyuta",'callback_data'=>"xizm-1320uc-PUBGMOBILE-UC"]],[['text'=>"🔵 1800 = $uc1800 $valyuta",'callback_data'=>"xizm-1800uc-PUBGMOBILE-UC"]],[['text'=>"🔵 2125 = $uc2125 $valyuta",'callback_data'=>"xizm-2125uc-PUBGMOBILE-UC"]],[['text'=>"🔵 2460 = $uc2460 $valyuta",'callback_data'=>"xizm-2460uc-PUBGMOBILE-UC"]],[['text'=>"🔵 3950 = $uc3950 $valyuta",'callback_data'=>"xizm-3950uc-PUBGMOBILE-UC"]],[['text'=>"🔵 8100 = $uc8100 $valyuta",'callback_data'=>"xizm-8100uc-PUBGMOBILE-UC"]] ]])]); }
if($data=="fire"){ bot('editMessageText',['chat_id'=>$cid2,'message_id'=>$mid2,'text'=>"<b>🔴 FREE FIRE ALMAZ - bo'limiga hush kelibsiz!</b>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"100 💎 = $almaz100 $valyuta",'callback_data'=>"xizm-100almaz-FreeFire-Almaz"]],[['text'=>"210 💎 = $almaz210 $valyuta",'callback_data'=>"xizm-210almaz-FreeFire-Almaz"]],[['text'=>"530 💎 = $almaz530 $valyuta",'callback_data'=>"xizm-530almaz-FreeFire-Almaz"]],[['text'=>"1080 💎 = $almaz1080 $valyuta",'callback_data'=>"xizm-1080almaz-FreeFire-Almaz"]],[['text'=>"2200 💎 = $almaz2200 $valyuta",'callback_data'=>"xizm-2200almaz-FreeFire-Almaz"]], ]])]); }
if(mb_stripos($data,"xizm-")!==false){ $xiz=explode("-",$data)[1]; $ich=explode("-",$data)[2]; $val=explode("-",$data)[3]; $donnarx=file_get_contents("donat/$ich/$xiz.txt"); bot('editMessageText',['chat_id'=>$cid2,'message_id'=>$mid2,'text'=>"📦 <b>Donat tanlandi:</b>\n\n💵 <b>Miqdori:</b> $xiz\n💸 <b>Narxi:</b> $donnarx $valyuta\n\n📑 <i>Donat $ich ID'raqamingiz orqali amalga oshiriladi.</i>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"✅ Tanlash",'callback_data'=>"tanla-$xiz-$ich-$val"]], [['text'=>"◀️ Orqaga",'callback_data'=>"ucpubg"]], ]])]); }
if(mb_stripos($data,"tanla-")!==false){ $ex=explode("-",$data); $xiz=$ex[1]; $ich=$ex[2]; $val=$ex[3]; $kabinet=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE id = $cid2")); $donnarx=file_get_contents("donat/$ich/$xiz.txt"); $yetmadi=$donnarx-$kabinet['balance']; if($kabinet['balance']>=$donnarx){ bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); bot('SendMessage',['chat_id'=>$cid2,'text'=>"<b><u>Botga $ich ID raqamingizni yuboring:</u></b>",'parse_mode'=>'html','reply_markup'=>$ort]); file_put_contents("user/$chat_id.step","next-$xiz-$ich-$val"); exit(); }else{ bot('SendMessage',['chat_id'=>$cid2,'text'=>"<b>🤷🏻‍♂ Hisobingizga $yetmadi so'm yetishmadi!\n\n<i>Hisobingizni to'ldirib qayta urining:</i></b>",'parse_mode'=>'html']); exit(); } }
if(mb_stripos($step,"next-")!==false){ $ex=explode("-",$step); $xiz=$ex[1]; $ich=$ex[2]; $val=$ex[3]; $rew13=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE id = $cid")); $pul13=$rew13['balance']; bot('SendMessage',['chat_id'=>$cid,'text'=>"<b>⛔ Donatni tasdiqlashdan oldin, quyidagi ma'lumotlarni tekshirib chiqing:\n\n🎮 O'yin turi:</b> <i>$ich $val</i>\n💳 <b>Donat miqdori:</b> <i>$xiz</i>\n💵 <b>Sizning balansingiz:</b> <i>$pul13 $valyuta</i>\n🆔 <b>$ich ID raqamingiz:</b> <code>$text</code>\n\n❔ Barchasi to'g'ri ekanligiga ishonch hosil qilgach pastdagi « <b>✅ Tasdiqlash</b> » tugmasini bosing.",'disable_web_page_preview'=>true,'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"✅ Tasdiqlash",'callback_data'=>"tasdiq-$ich-$xiz-$val-$text"]], [['text'=>"🚫 Bekor qilish",'callback_data'=>"bekor"]], ]])]); unlink("user/$cid.step"); exit(); }
if($data=="bekor"){ bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); bot('SendMessage',['chat_id'=>$cid2,'text'=>"<b>⛔️ Bekor qilindi!</b>",'parse_mode'=>'html','reply_markup'=>$menu]); exit(); }
if(mb_stripos($data,"tasdiq-")!==false){ $ex=explode("-",$data); $ich=$ex[1]; $xiz=$ex[2]; $val=$ex[3]; $ids=$ex[4]; $rew13=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE id = $cid2")); $narxi=file_get_contents("donat/$ich/$xiz.txt"); $ayir=$rew13['balance']-$narxi; mysqli_query($connect,"UPDATE users SET balance = '$ayir' WHERE id = $cid2"); bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); bot('SendMessage',['chat_id'=>$cid2,'text'=>"<b>✅ Donat bo'yicha so'rovingiz adminga yuborildi.\n\n$ich ID raqamingiz:</b> <code>$ids</code>\n\n<i>ℹ️ Tez orada sizning $ich $val hisobingizga $xiz tushgani haqida xabar beramiz.</i>",'parse_mode'=>'html','reply_markup'=>$menu]); bot('SendMessage',['chat_id'=>$admin,'text'=>"<b>✅ Yangi donat xizmati.\n\n👤 Donat egasi:</b> <i><a href='tg://user?id=$cid2'>$cid2</a></i>\n🎮 <b>O'yin turi:</b> <i>$ich $val</i>\n💳 <b>Donat miqdori:</b> <i>$xiz</i>\n🆔 <b>$ich ID raqami:</b> <code>$ids</code>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"✅ Tasdiqlash",'callback_data'=>"donaton-$ich-$xiz-$val-$ids-$cid2"]], [['text'=>"🚫 Bekor qilish",'callback_data'=>"bekor"]], ]])]); exit(); }
if(mb_stripos($data,"donaton-")!==false){ $ex=explode("-",$data); $ich=$ex[1]; $xiz=$ex[2]; $val=$ex[3]; $ids=$ex[4]; $donatchi=$ex[5]; bot('SendMessage',['chat_id'=>$donatchi,'text'=>"<b>✅ Donat bo'yicha so'rovingiz qabul qilindi.</b>\n\n<i>ℹ️ $ich $val hisobingizga $xiz tushurib berildi.</i>",'parse_mode'=>'html','reply_markup'=>$menu]); bot('SendMessage',['chat_id'=>$admin,'text'=>"<b>✅ Donat bo'yicha so'rov qabul qilindi.\n\n👤 Donat egasi:</b> <i><a href='tg://user?id=$donatchi'>$donatchi</a></i>",'parse_mode'=>'html','reply_markup'=>$menu]); }

// Buyurtma holati
if($text=="🛒 𝔹𝕦𝕪𝕦𝕣𝕥𝕞𝕒 𝕩𝕠𝕝𝕒𝕥𝕚" || $text=="/order" and joinchat($cid)==1){
    $rew14=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM myorder WHERE user_id = $cid"));
    if(!$rew14){ sms($cid,"❗️Sizda faol buyurtmalar yoʻq.",json_encode(['inline_keyboard'=>[[['text'=>"🔎 Izlab topish",'callback_data'=>"bytopish"]]]])); }
    else{ $rew14=mysqli_query($connect,"SELECT * FROM myorder WHERE user_id = $cid"); while($my14=mysqli_fetch_assoc($rew14)){ $k[]=["text"=>$my14['order_id'],"callback_data"=>"idby-".$my14['order_id']]; } $keysboard2=array_chunk($k,4); $keysboard2[]=[['text'=>"🔎 Buyurtma ma'lumoti","callback_data"=>"bytopish"]]; sms($cid,"🛍️ Barcha buyurtmalaringiz!",json_encode(['inline_keyboard'=>$keysboard2])); }
}
if(mb_stripos($data,"idby-")!==false){ $ex=explode("-",$data); $text15=$ex[1]; $rew15=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM orders WHERE order_id = $text15")); $ori=$rew15['api_order']; $prov=$rew15['provider']; $ap=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM providers WHERE id = $prov")); $ourl=$ap['api_url']; $okey=$ap['api_key']; $s=json_decode(get($ourl."?key=".$okey."&action=status&order=$ori"),1); $son=$s['remains']; $response=$rew15['status']; if($response=="Completed")$status="✅ Bajarilgan"; elseif($response=="In progress")$status="♻️ Jarayonda"; elseif($response=="Partial")$status="⭕ Qisman bajarilgan"; elseif($response=="Pending")$status="⏰ Kutilmoqda"; elseif($response=="Processing")$status="🔁 Qayta ishlanmoqda"; elseif($response=="Canceled")$status="❌ Bekor qilingan"; if(!$rew15 or $s['error']){ sms($cid,"❌ Buyurtma topilmadi!",$m); }else{ del(); sms($cid2,"<b>✅ Buyurtma topildi!</b>\n\n<b>📯 Buyurtma holati:</b> $status\n<b>🔎 Qoldiq miqdori:</b> $son ta",null); } }

// Nomer olish
if($text=="📞 ℕ𝕠𝕞𝕖𝕣 𝕠𝕝𝕚𝕤𝕙"){ bot('sendMessage',['chat_id'=>$cid,'text'=>"❗️Bo'limdan foydalanish uchun ushbu shartlarga roziligingizni bildiring\n\n- Sizga virtual nomer berilganda uni bemalol almashtirishingiz yoki bekor qilishingiz mumkin bo'ladi\n- Agar sizga sms kod kelsa virtual nomerni boshqa almashtirolmaysiz va nomer uchun pul yechiladi\n- Agarda kelgan kod notog'ri bo'lsa 20 daqiqa ichida yangi sms kod so'rashingiz mumkin\n- Telegram uchun nomer olganingizda Kod telegram orqali yuborildi deyilgan xabar chiqsa nomerni darhol bekor qiling!\n\n☝️ Yuqoridagi holatlar uchun da'volar qabul qilinmaydi",'parse_mode'=>"html",'reply_markup'=>json_encode(['remove_keyboard'=>true,'inline_keyboard'=>[[['text'=>"✅ Roziman",'callback_data'=>"hop"]],[['text'=>"❌ Bekor qilish",'callback_data'=>"menu_tolov"]]]])]); }

// Nomer olish - davlatlar
if($data=="hop"){
    $url15=json_decode(file_get_contents("https://api.sms-activate.org/stubs/handler_api.php?api_key=$simkey&action=getCountries"),true);
    $urla15=file_get_contents("https://api.sms-activate.org/stubs/handler_api.php?api_key=$simkey&action=getCountries");
    if($urla15=="BAD_KEY" or $urla15=="NO_KEY"){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"⚠️ Botga API kalit ulanmagan!",'show_alert'=>true]); }
    else{
        $key=[];
        $countries=["Russia"=>"🇷🇺 Rossiya","Ukraine"=>"🇺🇦 Ukraina","Kazakhstan"=>"🇰🇿 Qozog'iston","China"=>"🇨🇳 Xitoy","Philippines"=>"🇵🇭 Filippin","Myanmar"=>"🇲🇲 Myanma","Indonesia"=>"🇮🇩 Indoneziya","Malaysia"=>"🇲🇾 Malayziya","Kenya"=>"🇰🇪 Keniya","Tanzania"=>"🇹🇿 Tanzaniya"];
        for($i=0;$i<10;$i++){
            $eng=$url15["$i"]['eng'];
            $n=$countries[$eng]??$eng;
            $id15=$url15["$i"]['id'];
            $key[]=["text"=>"$n",'callback_data'=>"raqam=tg=ig=fb=tw=vi=oi=ts=go=$id15=$n"];
        }
        $key1=array_chunk($key,2);
        $key1[]=[["text"=>"1/6","callback_data"=>"null"],['text'=>"⏭️",'callback_data'=>"davlat2"]];
        $key1[]=[['text'=>"⏮️ Orqaga","callback_data"=>"orqa"]];
        bot('EditMessageText',['chat_id'=>$cid2,'message_id'=>$mid2,'text'=>"*Nomer olish uchun davlatlar ro'yxati:*",'parse_mode'=>'markdown','reply_markup'=>json_encode(['inline_keyboard'=>$key1])]);
    }
}

// Nomer sotib olish
if(stripos($data,"olish=")!==false){
    $xiz15=explode("=",$data)[1]; $id15=explode("=",$data)[2]; $op15=explode("=",$data)[3]; $pric15=explode("=",$data)[4]; $davlat15=explode("=",$data)[5];
    $result=mysqli_query($connect,"SELECT * FROM users WHERE id = $cid2"); $row15=mysqli_fetch_assoc($result); $foyid15=$row15['user_id']; $pul15=$row15['balance'];
    if($row15['balance']>=$pric15){
        $arrContextOptions=["ssl"=>["verify_peer"=>false,"verify_peer_name"=>false]];
        $response15=file_get_contents("https://api.sms-activate.org/stubs/handler_api.php?api_key=$simkey&action=getNumber&service=$xiz15&country=$id15&operator=$op15",false,stream_context_create($arrContextOptions));
        $pieces15=explode(":",$response15); $simid15=$pieces15[1]; $phone15=$pieces15[2];
        if($response15=="NO_NUMBERS"){ $msgs15="❌ Bu tarmoq uchun nomer mavjud emas!"; }
        elseif($response15=="NO_BALANCE"){ $msgs15="⚠️ Xatolik yuz berdi!"; }
        if($response15=="NO_NUMBERS" or $response15=="NO_BALANCE"){ bot("answerCallbackQuery",["callback_query_id"=>$update->callback_query->id,'text'=>$msgs15,"show_alert"=>true]); }
        elseif(mb_stripos($response15,"ACCESS_NUMBER")!==false){
            $miqdor15=$row15['balance']-$pric15; mysqli_query($connect,"UPDATE users SET balance=$miqdor15 WHERE id =$cid2");
            bot('editmessagetext',['chat_id'=>$cid2,'message_id'=>$mid2,'text'=>"\n🛎 *Sizga nomer berildi\n🌍 Davlat: $davlat15\n💸 Narxi: $pric15 so'm\n📞 Nomeringiz: +$phone15\n\nNusxalash:* `$phone15`\n\n*📨 Kodni olish uchun « 📩 SMS-kod olish » tugmasini bosing!*",'parse_mode'=>'markdown','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"📩 SMS-kod olish",'callback_data'=>"pcode_".$simid15."_".$pric15]], [['text'=>"❌ Bekor qilish",'callback_data'=>"otmena_".$simid15."_".$pric15]], ]])]);
            bot('sendMessage',['chat_id'=>$proof,'text'=>"📞 Yangi nomer olindi: <code>+$phone15</code>\n\n💰 Nomer narxi: $pric15 so'm\n\n👤 Buyurtmachi raqami $foyid15",'parse_mode'=>'html']);
        }
    }else{ bot("answerCallbackQuery",["callback_query_id"=>$update->callback_query->id,'text'=>"❗Sizda mablag' yetarli emas!","show_alert"=>true]); }
}

// SMS kod olish
if(stripos($data,"pcode_")!==false){ $ex=explode("_",$data); $simid16=$ex[1]; $so16=$ex[2]; $sims=file_get_contents("simcard.txt"); if(mb_stripos($sims,$simid16)!==false){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"❌ Kech qoldingiz!",'show_alert'=>true]); exit(); }else{ $response16=file_get_contents("https://api.sms-activate.org/stubs/handler_api.php?api_key=$simkey&action=getStatus&id=$simid16"); if(mb_stripos($response16,"STATUS_OK")!==false){ $pieces16=explode(":",$response16); $smskod=$pieces16[1]; bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); bot('sendMessage',['chat_id'=>$cid2,'text'=>"📩 *SMS keldi!\n\n🔢 KOD:* `$smskod`",'parse_mode'=>'markdown']); }elseif($response16=="STATUS_CANCEL"){ bot("answerCallbackQuery",["callback_query_id"=>$update->callback_query->id,'text'=>"✅ Balansingizga $so16 so'm qaytarildi!","show_alert"=>true]); $result16=mysqli_query($connect,"SELECT * FROM users WHERE id = $cid2"); $row16=mysqli_fetch_assoc($result16); $miqdor16=$so16+$row16['balance']; mysqli_query($connect,"UPDATE users SET balance=$miqdor16 WHERE id =$cid2"); file_put_contents("simcard.txt","\n".$simid16,FILE_APPEND); }else{ bot("answerCallbackQuery",["callback_query_id"=>$update->callback_query->id,'text'=>"⏰ SMS kutilmoqda!","show_alert"=>true]); } } }
if(stripos($data,"otmena_")!==false){ $simid16=explode("_",$data)[1]; $so16=explode("_",$data)[2]; $sims=file_get_contents("simcard.txt"); $response16=file_get_contents("https://api.sms-activate.org/stubs/handler_api.php?api_key=$simkey&action=setStatus&status=8&id=$simid16"); if(mb_stripos($sims,$simid16)!==false){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"❌ Kech qoldingiz!",'show_alert'=>true]); exit(); }else{ if(mb_stripos($response16,"ACCESS_CANCEL")!==false){ bot("answerCallbackQuery",["callback_query_id"=>$update->callback_query->id,'text'=>"✅ Balansingizga $so16 so'm qaytarildi","show_alert"=>true]); $result16=mysqli_query($connect,"SELECT * FROM users WHERE id = $cid2"); $row16=mysqli_fetch_assoc($result16); $miqdor16=$so16+$row16['balance']; mysqli_query($connect,"UPDATE users SET balance=$miqdor16 WHERE id =$cid2"); file_put_contents("simcard.txt","\n".$simid16,FILE_APPEND); }else{ bot("answerCallbackQuery",["callback_query_id"=>$update->callback_query->id,'text'=>"❗ Kuting....","show_alert"=>true]); } } }

// Tarif
if($text=="/tarif"){ sms($cid,"👉 Barcha ta'riflar",keyboard([[['text'=>"📝 Ta'riflar",'url'=>"https://".$_SERVER['HTTP_HOST']."/services"]]])); }

// Taymerlar
if((stripos($data,"ordered=")!==false)){ $n=explode("=",$data)[1]; $n2=explode("=",$data)[2]; $a=mysqli_query($connect,"SELECT * FROM services WHERE service_id= '$n'"); while($s=mysqli_fetch_assoc($a)){ $nam=base64_decode($s['service_name']); $sid=$s['service_id']; $narx=$s['service_price']; $curr=$s['api_currency']; $ab=$s['service_desc']?$s['service_desc']:null; $api=$s['api_service']; $type=$s['service_type']; $spi=$s['service_api']; $min=$s["service_min"]; $max=$s["service_max"]; } $ap=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM providers WHERE id = $api")); $surl=$ap['api_url']; $skey=$ap['api_key']; if($curr=="USD")$fr=get("set/usd"); elseif($curr=="RUB")$fr=get("set/rub"); elseif($curr=="INR")$fr=get("set/inr"); elseif($curr=="TRY")$fr=get("set/try"); else $fr=1; $abs=$ab?"\n".base64_decode($ab)."":null; if($type=="Default" or $type=="default") $abdesc="🔽 Minimal buyurtma: $min ta\n🔼 Maksimal buyurtma: $max ta\n\n$abs"; else $abdesc=$abs; if(empty($min) or empty($max)){ bot('answerCallbackQuery',['callback_query_id'=>$update->callback_query->id,'text'=>"⚠️ Nimadir xato ketdi qaytadan urining.",'show_alert'=>true]); }else{ edit($chat_id,$message_id,"\n<b>$nam</b>\n\n🔑 Xizmat IDsi: <code>$sid</code>\n💵 Narxi (1000 ta) - $narx so'm\n\n$abdesc\n\n",json_encode([inline_keyboard=>[ [['text'=>"✅ Tanlash",'callback_data'=>"order=$spi=$min=$max=".$narx."=$type=".$api."=$sid"]], [['text'=>"⏪ Orqaga",'callback_data'=>"tanla2=$n2"]], ]])); exit; } }
if((stripos($data,"order=")!==false)){ $oid=explode("=",$data)[1]; $omin=explode("=",$data)[2]; $omax=explode("=",$data)[3]; $orate=explode("=",$data)[4]; $otype=explode("=",$data)[5]; $prov=explode("=",$data)[6]; $serv=explode("=",$data)[7]; if($otype=="Default" or $otype=="default"){ del(); sms($chat_id,"⬇️ Kerakli buyurtma miqdorini kiriting:",$ort); put("user/$chat_id.step","order=default=sp1"); put("user/$chat_id.params","$oid=$omin=$omax=$orate=$prov=$serv"); put("user/$chat_id.si",$oid); exit; }elseif($otype=="Package"){ del(); sms($chat_id,"📎 Kerakli havolani kiriting (https://):",$ort); put("user/$chat_id.step","order=package=sp2=1=$orate"); put("user/$chat_id.params","$oid=$omin=$omax=$orate=$prov=$serv"); put("user/$chat_id.si",$oid); exit; } }
$s17=explode("=",$step);
if($s17[0]=="order" and $s17[1]=="default" and $s17[2]=="sp1" and is_numeric($text) and joinchat($cid)==1){ $p17=explode("=",get("user/$cid.params")); $narxi17=$p17[3]/1000*$text; if($text>=$p17[1] and $text<=$p17[2]){ $rew17=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE id = $cid")); if($rew17['balance']>=$narxi17){ sms($cid,"\n🛍️ $text saqlandi endi kerakli havolani yuboring.\n\n⚠️ Sahifangiz ochiq (ommaviy) boʻlishi kerak!",$ort); put("user/$cid.step","order=$s17[1]=sp2=$text=$narxi17"); put("user/$cid.qu",$text); exit; }else{ sms($cid,"❌ Yetarli mablag' mavjud emas\n💰 Narxi: $narxi17 so'm\n\nBoshqa miqdor kiritib ko'ring:",null); exit; } }else{ sms($cid,"\n⚠️ Buyurtma miqdorini notog'ri kiritilmoqda\n\n ⬇️ Minimal buyurtma: $p17[1]\n ⬆️ Maksimal: $p17[2]\n\n Boshqa miqdor kiriting",null); exit; } }
if(($s17[0]=="order" and ($s17[1]=="default" or $s17[1]=="package") and $s17[2]=="sp2" and joinchat($cid)==1)){ if($s17[1]=="default") $pc17="🔢 Buyurtma miqdori: $s17[3] ta"; $rew17=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE id = $cid")); if($rew17['balance']>=$s17[4]){ if((mb_stripos($tx,"https://")!==false) or (mb_stripos($text,"@")!==false)){ sms($cid,"\n➡️ Malumotlarni o'qib chiqing:\n\n💵 Buyurtma narxi: $s17[4] so'm\n📎 Buyurtma manzili: $text\n$pc17\n\n⚠️ Malumotlar to'g'ri bo'lsa (✅ Tasdiqlash) tugmasiga bosing",json_encode(['inline_keyboard'=>[[['text'=>"✅ Tasdiqlash",'callback_data'=>"checkorder=".uniqid()]]]]) ); put("user/$cid.step","order=$s17[1]=sp3=$s17[3]=$s17[4]=$text"); put("user/$cid.ur",$text); exit; }else{ sms($cid,"⚠️ Havola notog'ri\nQaytadan harakat qiling",null); } }else{ sms($cid,"❌ Yetarli mablag' mavjud emas",$ort); } }
$sc17=explode("=",get("user/$chat_id.step"));
if((stripos($data,"checkorder=")!==false and $sc17[0]=="order" and ($sc17[1]=="default" or $sc17[1]=="package") and $sc17[2]=="sp3" and joinchat($chat_id)==1)){ $rew17=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE id = $chat_id")); if($rew17['balance']>=$sc17[4]){ $sp17=explode("=",get("user/$chat_id.params")); $mprovider=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM providers WHERE id = ".$sp17[4]." ")); $surl=$mprovider['api_url']; $skey=$mprovider['api_key']; $j17=json_decode(get($surl."?key=".$skey."&action=add&service=".get("user/$chat_id.si")."&link=".get("user/$chat_id.ur")."&quantity=".get("user/$chat_id.qu")),1); $jid17=$j17['order']; $jer17=$j17['error']; if(empty($jid17)){ bot('answerCallbackQuery',['callback_query_id'=>$cqid,'text'=>"⚠️ Noma'lum xatolik yuz berdi\n\nKeyinroq urinib ko'ring",'show_alert'=>1]); sms($chat_id,"🖥️ Asosiy menyudasiz",$menu); unlink("user/$chat_id.step"); unlink("user/$chat_id.params"); exit; }else{ $oe=mysqli_num_rows(mysqli_query($connect,"SELECT * FROM orders")); $or=$oe+1; $sav=date("Y.m.d H:i:s"); mysqli_query($connect,"INSERT INTO myorder(`order_id`,`user_id`,`retail`,`status`,`service`,`order_create`,`last_check`) VALUES ('$or','$chat_id','$sc17[4]','Pending','$sp17[5]','$sav','$sav');"); mysqli_query($connect,"INSERT INTO orders(`api_order`,`order_id`,`provider`,`status`) VALUES ('$jid17','$or','$sp17[4]','Pending');"); $rew17b=mysqli_fetch_assoc(mysqli_query($connect,"SELECT * FROM users WHERE id = $cid")); $order17=str_replace(["{order}","{order_api}"],["$or","$jid17"],enc("decode",$setting['orders'])); sms($chat_id,$order17,null); $miqdor17=$rew17['balance']-$sc17[4]; mysqli_query($connect,"UPDATE users SET balance=$miqdor17 WHERE id =$chat_id"); unlink("user/$chat_id.step"); del(); exit; } } }

// Foydalanuvchi qo'shish
if($message){ adduser($cid); }

// Main
if(($data=="main") and (joinchat($cid2)==1)){ bot('AnswerCallbackQuery',['callback_query_id'=>$qid,'text'=>"✅ Asosiy menyudasiz!",'show_alert'=>false]); bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); bot('sendmessage',['chat_id'=>$cid2,'parse_mode'=>"html",'reply_markup'=>$m,'text'=>"🖥️ <b>Asosiy menyuga qaytdingiz.</b>"]); unlink("user/$cid2.step"); unlink("user/$cid2.ur"); unlink("user/$cid2.params"); unlink("user/$cid2.qu"); unlink("user/$cid2.si"); exit(); }

// Yopish
if($data=="yopish"){ bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); }

?>
