<?php
session_start();
date_default_timezone_set("Asia/Tashkent");
$time = date('H:i');
ob_start();

define('API_KEY', "8674893543:AAEmbCiJkWchGiSgXzXrcL_NYZRFl75GEbw");

$admin     = "8537782289";
$admin2    = "8674893543";
$admins    = [$admin, $admin2];

$proof     = "@QoraCoders_Uzb";
$simkey    = "8395fA936b4874292c214df2A4c9Ae8c";
$simfoiz   = "50";
$simrub    = "130";
$channel   = "130";
$me        = "🛎";
$smm12     = "https://t.me/QoraCoders_Uzb/1";
$valyuta   = "so'm";
$paychannel = "@QoraCoders_Uzb";

// ─── SQLite DB (MySQL o'rniga) ────────────────────────────────────
@mkdir("/app/data", 0777, true);
$pdo = new PDO('sqlite:/app/data/bot.db');
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$pdo->exec("PRAGMA journal_mode=WAL;");

$pdo->exec("CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    status TEXT DEFAULT 'active',
    balance REAL DEFAULT 0,
    outing REAL DEFAULT 0,
    api_key TEXT,
    referal TEXT
)");
$pdo->exec("CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, orders TEXT, welcome TEXT, about TEXT)");
$pdo->exec("CREATE TABLE IF NOT EXISTS percent (id INTEGER PRIMARY KEY, percent REAL DEFAULT 0)");
$pdo->exec("CREATE TABLE IF NOT EXISTS send (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time1 TEXT, time2 TEXT, time3 TEXT, time4 TEXT, time5 TEXT,
    start_id INTEGER DEFAULT 0, stop_id TEXT, admin_id TEXT,
    message_id TEXT, reply_markup TEXT, step TEXT
)");
$pdo->exec("CREATE TABLE IF NOT EXISTS providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, api_url TEXT, api_key TEXT
)");
$pdo->exec("CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id TEXT, service_name TEXT, service_price REAL,
    service_status TEXT DEFAULT 'on', service_type TEXT DEFAULT 'Default',
    service_api INTEGER, service_min INTEGER, service_max INTEGER,
    service_desc TEXT, api_service TEXT, api_currency TEXT DEFAULT 'UZS', category_id TEXT
)");
$pdo->exec("CREATE TABLE IF NOT EXISTS categorys (
    id INTEGER PRIMARY KEY AUTOINCREMENT, category_id TEXT, category_name TEXT
)");
$pdo->exec("CREATE TABLE IF NOT EXISTS cates (
    id INTEGER PRIMARY KEY AUTOINCREMENT, cate_id TEXT, name TEXT, category_id TEXT
)");
$pdo->exec("CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_order TEXT, order_id TEXT, provider TEXT, status TEXT DEFAULT 'Pending'
)");
$pdo->exec("CREATE TABLE IF NOT EXISTS myorder (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT, user_id TEXT, retail REAL,
    status TEXT DEFAULT 'Pending', service TEXT, order_create TEXT, last_check TEXT
)");
$pdo->exec("INSERT OR IGNORE INTO settings (id) VALUES (1)");
$pdo->exec("INSERT OR IGNORE INTO percent (id, percent) VALUES (1, 0)");

// ─── DB yordamchi funksiyalar ─────────────────────────────────────
function db_fetch($sql) {
    global $pdo;
    try { return $pdo->query($sql)->fetch(PDO::FETCH_ASSOC) ?: null; }
    catch(Exception $e){ return null; }
}
function db_fetchall($sql) {
    global $pdo;
    try { return $pdo->query($sql)->fetchAll(PDO::FETCH_ASSOC) ?: []; }
    catch(Exception $e){ return []; }
}
function db_count($sql) {
    global $pdo;
    try { return count($pdo->query($sql)->fetchAll()); }
    catch(Exception $e){ return 0; }
}
function db_exec($sql) {
    global $pdo;
    try { $pdo->exec($sql); return true; }
    catch(Exception $e){ return false; }
}

$connect = $pdo; // moslik uchun

$bot = bot('getMe')->result->username;

// ─── YORDAMCHI FUNKSIYALAR ────────────────────────────────────────
function enc($var, $exception){
    if($var=="encode") return base64_encode($exception);
    elseif($var=="decode") return base64_decode($exception);
}
function keyboard($a=[]){ return json_encode(['inline_keyboard'=>$a]); }
function api_query($s){
    $qas = ["ssl"=>["verify_peer"=>false,"verify_peer_name"=>false]];
    $c = file_get_contents($s, false, stream_context_create($qas));
    return $c ? $c : json_encode(['balance'=>" ?"]);
}
function arr($p){
    $s = db_fetch("SELECT * FROM `providers` WHERE id = $p");
    $data = json_decode(file_get_contents($s['api_url']."?key=".$s['api_key']."&action=services"),1);
    $values=[]; $new_arr=[]; $co=0;
    foreach($data as $value){
        if(!in_array($value['category'],$new_arr)){
            $new_arr[]=$value['category']; $co++;
            $values[]=['id'=>$co,'name'=>$value['category']];
        }
    }
    return $values ? json_encode(['count'=>$co,'results'=>$values]) : json_encode(["error"=>1]);
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
function number($a){ return number_format($a,00,' ',' '); }
function del(){
    global $cid,$mid,$chat_id,$message_id;
    return bot('deleteMessage',['chat_id'=>$chat_id.$cid,'message_id'=>$message_id.$mid]);
}
function edit($id,$mid,$tx,$m){
    return bot('editMessageText',['chat_id'=>$id,'message_id'=>$mid,'text'=>"<b>$tx</b>",'parse_mode'=>"HTML",'disable_web_page_preview'=>true,'reply_markup'=>$m]);
}
function sms($id,$tx,$m){
    return bot('sendMessage',['chat_id'=>$id,'text'=>"<b>$tx</b>",'parse_mode'=>"HTML",'disable_web_page_preview'=>true,'reply_markup'=>$m]);
}
function get($h){ return @file_get_contents($h); }
function put($h,$r){ file_put_contents($h,$r); }
function generate(){
    $arr=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','R','S','T','U','V','X','Y','Z','1','2','3','4','5','6','7','8','9','0'];
    $pass="";
    for($i=0;$i<7;$i++) $pass.=$arr[rand(0,count($arr)-1)];
    return $pass;
}
function adduser($cid){
    $row = db_fetch("SELECT * FROM users WHERE id = '$cid'");
    if(!$row){
        $key=md5(uniqid()); $referal=generate();
        $new = db_count("SELECT * FROM users") + 1;
        db_exec("INSERT INTO users(user_id,id,status,balance,outing,api_key,referal) VALUES ('$new','$cid','active','0','0','$key','$referal')");
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
    $array=["inline_keyboard"];
    $get=@file_get_contents("set/channel");
    $ex=explode("\n",$get);
    if(!$get) return true;
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
    }else{ return true; }
}

// ─── UPDATE PARSE ─────────────────────────────────────────────────
$update     = json_decode(file_get_contents('php://input'));
$message    = $update->message;
$mid        = $message->message_id;
$msgs       = json_decode(@file_get_contents('msgs.json'),true);
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
$botdel     = $update->my_chat_member->new_chat_member;
$botdel_id  = $update->my_chat_member->from->id;
$userstatus = $botdel->status;
$step  = get("user/$cid.step");
$stepc = get("user/$chat_id.step");

// ─── DIREKTORIYALAR ───────────────────────────────────────────────
@mkdir("user"); @mkdir("set"); @mkdir("odam");
@mkdir("foydalanuvchi"); @mkdir("foydalanuvchi/yurak");
@mkdir("foydalanuvchi/hisob"); @mkdir("foydalanuvchi/til");
@mkdir("donat"); @mkdir("donat/PUBGMOBILE"); @mkdir("donat/FreeFire");

// ─── DONAT NARXLARI ───────────────────────────────────────────────
$pubg_prices = ["60uc"=>"12000","120uc"=>"24000","180uc"=>"36000","325uc"=>"63000",
    "385uc"=>"75000","660uc"=>"120000","720uc"=>"132000","985uc"=>"180000",
    "1320uc"=>"245000","1800uc"=>"340000","2125uc"=>"403000","2460uc"=>"470000",
    "3950uc"=>"750000","8100uc"=>"1500000"];
$ff_prices = ["100almaz"=>"15000","210almaz"=>"30000","530almaz"=>"75000",
    "1080almaz"=>"150000","2200almaz"=>"300000"];
foreach($pubg_prices as $k=>$v) if(!file_exists("donat/PUBGMOBILE/$k.txt")) file_put_contents("donat/PUBGMOBILE/$k.txt",$v);
foreach($ff_prices as $k=>$v) if(!file_exists("donat/FreeFire/$k.txt")) file_put_contents("donat/FreeFire/$k.txt",$v);

$uc60=get("donat/PUBGMOBILE/60uc.txt"); $uc120=get("donat/PUBGMOBILE/120uc.txt");
$uc180=get("donat/PUBGMOBILE/180uc.txt"); $uc325=get("donat/PUBGMOBILE/325uc.txt");
$uc385=get("donat/PUBGMOBILE/385uc.txt"); $uc660=get("donat/PUBGMOBILE/660uc.txt");
$uc720=get("donat/PUBGMOBILE/720uc.txt"); $uc985=get("donat/PUBGMOBILE/985uc.txt");
$uc1320=get("donat/PUBGMOBILE/1320uc.txt"); $uc1800=get("donat/PUBGMOBILE/1800uc.txt");
$uc2125=get("donat/PUBGMOBILE/2125uc.txt"); $uc2460=get("donat/PUBGMOBILE/2460uc.txt");
$uc3950=get("donat/PUBGMOBILE/3950uc.txt"); $uc8100=get("donat/PUBGMOBILE/8100uc.txt");
$almaz100=get("donat/FreeFire/100almaz.txt"); $almaz210=get("donat/FreeFire/210almaz.txt");
$almaz530=get("donat/FreeFire/530almaz.txt"); $almaz1080=get("donat/FreeFire/1080almaz.txt");
$almaz2200=get("donat/FreeFire/2200almaz.txt");

if(!file_exists("foydalanuvchi/yurak/$cid.txt")) file_put_contents("foydalanuvchi/yurak/$cid.txt","0");
if(!file_exists("foydalanuvchi/hisob/$cid.til")) file_put_contents("foydalanuvchi/hisob/$cid.til","uz");

$pul  = get("user/$chat_id.pul");
$til  = file_get_contents("foydalanuvchi/hisob/$cid.til");
$step = get("user/$cid.step");

// ─── MENYULAR ─────────────────────────────────────────────────────
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

$setting = db_fetch("SELECT * FROM `settings`");
if(in_array($cid,$admins) or in_array($chat_id,$admins)) $m=$menu_p;
else $m=$menu;

// ─── BOT O'CHIRILGANDA ────────────────────────────────────────────
if($botdel && $userstatus=="kicked"){
    db_exec("UPDATE `users` SET `status` = 'deactive' WHERE `id` = '$botdel_id'");
}

// ─── DEACTIVE TEKSHIRISH ──────────────────────────────────────────
if(isset($update)){
    $rew=db_fetch("SELECT * FROM users WHERE id = '$cid$chat_id'");
    if($rew && $rew['status']=="deactive") exit();
}

// ─── BOT MUZLATILGAN ──────────────────────────────────────────────
if($update && get("status.txt")=="frozen"){
    sms($cid.$chat_id,"🥶 Panel vaqtincha muzlatilgan",null);
}

// ─── ADMIN ────────────────────────────────────────────────────────
if($text=="📞 Nomer API balans" and in_array($cid,$admins)){
    $url=file_get_contents("https://api.sms-activate.org/stubs/handler_api.php?api_key=$simkey&action=getBalance");
    $h=explode(":",$url)[1];
    sms($cid,"📄 API: <code>sms-activate.org</code>\nAPI kalit: <code>$simkey</code>\nHisob: $h ₽",$panel);
    @unlink("user/$cid.step"); exit;
}
if($text=="🗄️ Boshqaruv" and in_array($cid,$admins)){
    sms($cid,"🖥️ Boshqaruv paneli",$panel); @unlink("user/$cid.step"); exit;
}
if($text=="📊 Statistika" and in_array($cid,$admins)){
    $users=db_fetchall("SELECT * FROM users"); $stat=count($users);
    $ordersList=db_fetchall("SELECT * FROM orders"); $stati=count($ordersList);
    $ac=0;$dc=0;$pc=0;$cc=0;$bc=0;$fc=0;$jc=0;$ppc=0;$cp=0;
    foreach($ordersList as $hi){
        if($hi['status']=="Pending")$pc++;
        elseif($hi['status']=="Completed")$cc++;
        elseif($hi['status']=="Canceled")$bc++;
        elseif($hi['status']=="Failed")$fc++;
        elseif($hi['status']=="In progress")$jc++;
        elseif($hi['status']=="Partial")$ppc++;
        elseif($hi['status']=="Processing")$cp++;
    }
    foreach($users as $h){ if($h['status']=="active")$ac++; elseif($h['status']=="deactive")$dc++; }
    $seco=db_count("SELECT * FROM services");
    sms($cid,"<b>📊 Statistika</b>\n• Jami foydalanuvchilar: $stat ta\n• Aktiv: $ac ta\n• O'chirilgan: $dc ta\n\n<b>📊 Buyurtmalar</b>\n• Jami: $stati ta\n• Bajarilgan: $cc ta\n• Kutilayotgan: $pc ta\n• Jarayonda: $jc ta\n• Bekor: $bc ta\n• Xato: $fc ta\n\n<b>📊 Xizmatlar:</b> $seco ta",keyboard([
        [['text'=>"♻️ Buyurtmalar holatini yangilash",'callback_data'=>"update=orders"]],
        [['text'=>"🏆 TOP 100 Balans",'callback_data'=>"preyting"],['text'=>"🏆 Top 100 Referal",'callback_data'=>"treyting"]],
    ]));
    @unlink("user/$cid.step");
}
if($text=="⚙️ Asosiy sozlamalar" and in_array($cid,$admins)){ sms($cid,$text,$panel2); }
if($text=="💵 Kursni o'rnatish" and in_array($cid,$admins)){
    sms($cid,"👉 Kerakli valyutasi tanlang:",json_encode(['inline_keyboard'=>[
        [['text'=>"AQSH dollari ($)",'callback_data'=>"course=usd"]],
        [['text'=>"Rossiya rubli (₽)",'callback_data'=>"course=rub"]],
        [['text'=>"Hindston rupiysi (₹)",'callback_data'=>"course=inr"]],
        [['text'=>"Turkiya lirasi (₺)",'callback_data'=>"course=try"]],
    ]]));
}
if(stripos($data,"course=")!==false){
    $val=explode("=",$data)[1]; $VAL=get("set/".$val) ?: 0;
    del(); sms($chat_id,"1 - ".strtoupper($val)." narxini kiriting:\n♻️ Joriy narx: $VAL so'm",$aort);
    put("user/$chat_id.step","course=$val");
}
if(mb_stripos($step,"course=")!==false and is_numeric($text)){
    $val=explode("=",$step)[1]; put("set/".$val,"$text");
    sms($cid,"✅ 1 - ".strtoupper($val)." narxi $text so'mga o'zgardi",$panel);
    @unlink("user/$cid.step");
}
if($text=="⚖️ Foizni o'rnatish" and in_array($cid,$admins)){
    $m2=db_fetch("SELECT * FROM percent WHERE id = 1"); $m2=$m2['percent']??0;
    sms($cid,"⭐ Foizni kiriting\n♻️ Joriy foiz: $m2%",$aort);
    put("user/$cid.step","updFoiz");
}
if($step=="updFoiz"){ if(is_numeric($text)){ db_exec("UPDATE percent SET percent = '$text' WHERE id = 1"); sms($cid,"✅ O'zgartirish bajarildi.",$panel); } put("user/$cid.step",""); }

if($text=="🔔 Xabar yuborish" and in_array($cid,$admins)){
    $row=db_fetch("SELECT * FROM `send`");
    if(!$row){ bot('sendMessage',['chat_id'=>$cid,'text'=>"<b>📤 Xabarni yuboring!</b>",'parse_mode'=>'html','reply_markup'=>$aort]); put("user/$cid.step","send"); }
    else{ bot('sendMessage',['chat_id'=>$cid,'text'=>"<b>📑 Yuborish jarayoni davom etmoqda.</b>",'parse_mode'=>'html','reply_markup'=>$panel]); }
}
if($step=="send" and in_array($cid,$admins)){
    $allUsers=db_fetchall("SELECT * FROM users"); $stat=count($allUsers);
    $lastUser=db_fetch("SELECT * FROM users WHERE user_id = '$stat'"); $user_id=$lastUser['id']??0;
    $time1=date('H:i',strtotime('+1 minutes')); $time2=date('H:i',strtotime('+2 minutes'));
    $time3=date('H:i',strtotime('+3 minutes')); $time4=date('H:i',strtotime('+4 minutes')); $time5=date('H:i',strtotime('+5 minutes'));
    $tugma=json_encode($update->message->reply_markup); $reply_markup=base64_encode($tugma);
    db_exec("INSERT INTO `send`(time1,time2,time3,time4,time5,start_id,stop_id,admin_id,message_id,reply_markup,step) VALUES ('$time1','$time2','$time3','$time4','$time5','0','$user_id','$admin','$mid','$reply_markup','send')");
    bot('sendMessage',['chat_id'=>$admin,'text'=>"<b>📋 Saqlandi! Xabar $time1 da yuboriladi!</b>",'parse_mode'=>'html','reply_markup'=>$panel]);
    @unlink("user/$cid.step");
}
$row2=db_fetch("SELECT * FROM `send`");
if($_GET['update']=="send"){
    $row1=$row2['time1'];$row2t=$row2['time2'];$row3=$row2['time3'];$row4=$row2['time4'];$row5=$row2['time5'];
    $start_id=$row2['start_id'];$stop_id=$row2['stop_id'];$admin_id=$row2['admin_id'];
    $mied=$row2['message_id'];$tugma=$row2['reply_markup'];
    $reply_markup=($tugma=="bnVsbA==")?"":(base64_decode($tugma)); $limit=150;
    if($time==$row1 or $time==$row2t or $time==$row3 or $time==$row4 or $time==$row5){
        $sendUsers=db_fetchall("SELECT * FROM `users` LIMIT $limit OFFSET $start_id");
        foreach($sendUsers as $a){
            $id=$a['id'];
            bot('forwardMessage',['chat_id'=>$id,'from_chat_id'=>$admin_id,'message_id'=>$mied,'disable_web_page_preview'=>true,'reply_markup'=>$reply_markup]);
            if($id==$stop_id){ bot('sendMessage',['chat_id'=>$admin_id,'text'=>"<b>✅ Xabar barcha foydalanuvchilarga yuborildi!</b>",'parse_mode'=>'html']); db_exec("DELETE FROM `send`"); exit; }
        }
        $t1=date('H:i',strtotime('+1 minutes'));$t2=date('H:i',strtotime('+2 minutes'));
        $t3=date('H:i',strtotime('+3 minutes'));$t4=date('H:i',strtotime('+4 minutes'));$t5=date('H:i',strtotime('+5 minutes'));
        db_exec("UPDATE `send` SET time1='$t1',time2='$t2',time3='$t3',time4='$t4',time5='$t5'");
        $get_id=$start_id+$limit; db_exec("UPDATE `send` SET start_id='$get_id'");
        bot('sendMessage',['chat_id'=>$admin_id,'text'=>"<b>✅ Yuborildi: $get_id</b>",'parse_mode'=>'html']);
    }
    echo json_encode(["status"=>true,"cron"=>"Sending message"]);
}
if($_GET['update']=="orders"){
    $ol=db_fetchall("SELECT * FROM orders WHERE status != 'Completed' AND status != 'Canceled' AND status != 'Failed'");
    foreach($ol as $ord){
        $ap=db_fetch("SELECT * FROM providers WHERE id = ".$ord['provider']); if(!$ap) continue;
        $s=json_decode(get($ap['api_url']."?key=".$ap['api_key']."&action=status&order=".$ord['api_order']),1);
        if($s['status']??false){ db_exec("UPDATE orders SET status='".$s['status']."' WHERE id=".$ord['id']); db_exec("UPDATE myorder SET status='".$s['status']."' WHERE order_id='".$ord['order_id']."'"); }
    }
    echo json_encode(["status"=>true]); exit;
}
if($data=="update=orders" and in_array($chat_id,$admins)){
    $ol=db_fetchall("SELECT * FROM orders WHERE status != 'Completed' AND status != 'Canceled' AND status != 'Failed'");
    $updated=0;
    foreach($ol as $ord){
        $ap=db_fetch("SELECT * FROM providers WHERE id = ".$ord['provider']); if(!$ap) continue;
        $s=json_decode(get($ap['api_url']."?key=".$ap['api_key']."&action=status&order=".$ord['api_order']),1);
        if($s['status']??false){ db_exec("UPDATE orders SET status='".$s['status']."' WHERE id=".$ord['id']); db_exec("UPDATE myorder SET status='".$s['status']."' WHERE order_id='".$ord['order_id']."'"); $updated++; }
    }
    bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"✅ $updated ta buyurtma yangilandi",'show_alert'=>true]);
}

// ─── START ────────────────────────────────────────────────────────
if($text=="/start"){
    adduser($cid);
    $ref=explode(" ",$text)[1];
    if($ref and $ref!=$cid){
        $refUser=db_fetch("SELECT * FROM users WHERE referal = '$ref'");
        if($refUser){ $bonus=get("set/refbonus")?:500; $newBal=$refUser['balance']+$bonus; db_exec("UPDATE users SET balance='$newBal' WHERE referal='$ref'"); bot('sendMessage',['chat_id'=>$refUser['id'],'text'=>"🎉 Referal bonus: +$bonus so'm",'parse_mode'=>'html']); }
    }
    sms($cid,"🖥️ Asosiy menyudasiz",$m); exit;
}

// ─── MENING HISOBIM ───────────────────────────────────────────────
if($text=="🔐 𝕄𝕖𝕟𝕚𝕟𝕘 𝕙𝕚𝕤𝕠𝕓𝕚𝕞"){
    $rew=db_fetch("SELECT * FROM users WHERE id = '$cid'");
    if(!$rew){ adduser($cid); $rew=db_fetch("SELECT * FROM users WHERE id = '$cid'"); }
    sms($cid,"👤 <b>Mening hisobim</b>\n\n🆔 ID: <code>$cid</code>\n💰 Balans: <b>".($rew['balance']??0)." so'm</b>\n🔗 Referal: <code>".($rew['referal']??'')."</code>",$m);
}

// ─── HISOBNI TO'LDIRISH ───────────────────────────────────────────
if($text=="💰 ℍ𝕚𝕤𝕠𝕓𝕟𝕚 𝕥𝕠'𝕝𝕕𝕚𝕣𝕚𝕤𝕙"){ sms($cid,"💰 Hisobni to'ldirish uchun admin bilan bog'laning:\n\n@QoraCoders_Uzb",$m); }

// ─── REFERAL ─────────────────────────────────────────────────────
if($text=="🚀 ℝ𝕖𝕗𝕖𝕣𝕒𝕝 𝕪𝕚ğ𝕚𝕤𝕙"){
    $rew=db_fetch("SELECT * FROM users WHERE id = '$cid'"); $ref2=$rew['referal']??generate();
    $bonus=get("set/refbonus")?:500;
    sms($cid,"🚀 <b>Referal tizimi</b>\n\nHar bir referal uchun: <b>$bonus so'm</b>\n\n🔗 Sizning havolangiz:\n<code>https://t.me/{$bot}?start=$ref2</code>",$m);
}

// ─── ADMIN PANEL ─────────────────────────────────────────────────
if($text=="☎️ 𝔸𝕕𝕞𝕚𝕟𝕚𝕤𝕥𝕣𝕒𝕥𝕠𝕣"){ if(in_array($cid,$admins)) sms($cid,"🖥️ Boshqaruv paneli",$panel); else sms($cid,"❌ Siz admin emassiz!",$m); }

// ─── API KALIT ────────────────────────────────────────────────────
if($text=="🤝 ℍ𝕒𝕞𝕜𝕠𝕣𝕝𝕚𝕜 (𝔸ℙ𝕀)"){
    $rew12=db_fetch("SELECT * FROM `users` WHERE id = '$cid'");
    sms($cid,"<b>⭐ Sizning API kalitingiz:\n<code>".$rew12['api_key']."</code>\n\n💵 API hisobi: <b>".$rew12['balance']."</b> so'm</b>",keyboard([[['text'=>"📝 Qo'llanma",'callback_data'=>"apidetail=qoll"]],[['text'=>"🔄 APIni yangilash",'callback_data'=>"apidetail=newkey"]]]));
}
if(stripos($data,"apidetail=")!==false){ $res12=explode("=",$data)[1]; if($res12=="newkey"){ $newkey=md5(uniqid()); db_exec("UPDATE users SET api_key = '$newkey' WHERE id = '$chat_id'"); $rew12=db_fetch("SELECT * FROM `users` WHERE id = '$chat_id'"); bot('editMessageText',['chat_id'=>$chat_id,'parse_mode'=>"html",'message_id'=>$message_id,'text'=>"<b>\n✅ API kalit yangilandi.\n\n<code>".$rew12['api_key']."</code>\n\n💵 API hisobi:\n<b>".$rew12['balance']."</b> so'm\n</b>",'reply_markup'=>keyboard([[['text'=>"📝 Qo'llanma",'callback_data'=>"apidetail=qoll"]],[['text'=>"🔄 APIni yangilash",'callback_data'=>"apidetail=newkey"]]]) ]); } }

// ─── BUYURTMA BERISH ──────────────────────────────────────────────
if($text=="🛍 𝔹𝕦𝕪𝕦𝕣𝕥𝕞𝕒 𝕓𝕖𝕣𝕚𝕤𝕙" and joinchat($cid)==1){
    bot('sendChatAction',['chat_id'=>$cid,'action'=>"typing"]);
    $catList=db_fetchall("SELECT * FROM `categorys`"); $c=count($catList); $k=[];
    foreach($catList as $s) $k[]=['text'=>"".enc("decode",$s['category_name']),'callback_data'=>"tanla1=".$s['category_id']];
    $keyboard2=array_chunk($k,1);
    $keyboard2[]=[['text'=>"🎟️ Donat Xizmati",'callback_data'=>"servis"]];
    $keyboard2[]=[['text'=>"🔥 Eng yaxshi xizmatlar ⚡️",'url'=>"https://".$_SERVER['HTTP_HOST']."/services"]];
    $kb=json_encode(['inline_keyboard'=>$keyboard2]);
    if($c) sms($cid,"✅ Xizmatlarimizni tanlaganingizdan xursandmiz!\n👇 Ijtimoiy tarmoqni tanlang.",$kb);
    else sms($cid,"⚠️ Tarmoqlar topilmadi.",null);
}
if($data=="absd" and joinchat($chat_id)==1){ $catList=db_fetchall("SELECT * FROM categorys"); $c=count($catList); $k=[]; foreach($catList as $s) $k[]=['text'=>enc("decode",$s['category_name']),'callback_data'=>"tanla1=".$s['category_id']]; if(!$c){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"⚠️ Tarmoqlar topilmadi!",'show_alert'=>true]); }else{ $keyboard2=array_chunk($k,1); $keyboard2[]=[['text'=>"🎟️ Donat Xizmati",'callback_data'=>"servis"]]; $kb=json_encode(['inline_keyboard'=>$keyboard2]); edit($chat_id,$mid2,"✅ Xizmatlarimizni tanlaganingizdan xursandmiz!\n👇 Ijtimoiy tarmoqni tanlang.",$kb); exit; } }
if(mb_stripos($data,"tanla1=")!==false and joinchat($chat_id)==1){ $n=explode("=",$data)[1]; $adds=json_decode(get("set/sub.json"),1); $adds['cate_id']=$n; put("set/sub.json",json_encode($adds)); $new_arr=[];$k=[]; $cateList=db_fetchall("SELECT * FROM cates WHERE category_id = $n"); $c=count($cateList); foreach($cateList as $s){ if(!in_array(enc("decode",$s['name']),$new_arr)){ $new_arr[]=enc("decode",$s['name']); $k[]=['text'=>"".enc("decode",$s['name']),'callback_data'=>"tanla2=".$s['cate_id']]; } } $keyboard2=array_chunk($k,1); $keyboard2[]=[['text'=>"⏪ Orqaga",'callback_data'=>"absd"]]; $kb=json_encode(['inline_keyboard'=>$keyboard2]); if(!$c){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"⚠️ Xizmat turlari topilmadi!",'show_alert'=>true]); }else{ edit($chat_id,$message_id,"⬇️ Kerakli xizmat turini tanlang:",$kb); exit; } }
if(mb_stripos($data,"tanla2=")!==false and joinchat($chat_id)==1){ $n=explode("=",$data)[1]; $k=[]; $srvList=db_fetchall("SELECT * FROM services WHERE category_id = '$n' AND service_status = 'on'"); $c=count($srvList); foreach($srvList as $s){ $narx=$s['service_price']; $k[]=['text'=>"".base64_decode($s['service_name'])." $narx - so'm",'callback_data'=>"ordered=".$s['service_id']."=".$n]; } $keyboard2=array_chunk($k,1); $adds=json_decode(get("set/sub.json"),1); $keyboard2[]=[['text'=>"⏪ Orqaga",'callback_data'=>"tanla1=".$adds['cate_id']]]; $kb=json_encode(['inline_keyboard'=>$keyboard2]); if(!$c){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"⚠️ Xizmatlar topilmadi!",'show_alert'=>true]); }else{ edit($chat_id,$message_id,"⬇️ Kerakli xizmatni tanlang:",$kb); exit; } }

// ─── DONAT ────────────────────────────────────────────────────────
if($data=="servis"){ bot('sendChatAction',['chat_id'=>$cid,'action'=>"typing"]); bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); bot('SendMessage',['chat_id'=>$cid2,'text'=>"<b>✅ Xizmatlarimizni tanlaganingizdan xursandmiz!\n👇 O'yinni tanlang:</b>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"🔵 PUBG UC",'callback_data'=>"ucpubg"],['text'=>"🔴 FREE FIRE ALMAZ",'callback_data'=>"fire"]] ]])]); exit(); }
if($data=="ucpubg"){ bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); bot('SendMessage',['chat_id'=>$cid2,'text'=>"<b>🔵 PUBG UC bo'limiga hush kelibsiz!</b>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"🔵 60 - $uc60 $valyuta",'callback_data'=>"xizm-60uc-PUBGMOBILE-UC"]],[['text'=>"🔵 120 - $uc120 $valyuta",'callback_data'=>"xizm-120uc-PUBGMOBILE-UC"]],[['text'=>"🔵 180 - $uc180 $valyuta",'callback_data'=>"xizm-180uc-PUBGMOBILE-UC"]],[['text'=>"🔵 325 - $uc325 $valyuta",'callback_data'=>"xizm-325uc-PUBGMOBILE-UC"]],[['text'=>"🔵 385 - $uc385 $valyuta",'callback_data'=>"xizm-385uc-PUBGMOBILE-UC"]],[['text'=>"🔵 660 - $uc660 $valyuta",'callback_data'=>"xizm-660uc-PUBGMOBILE-UC"]],[['text'=>"🔵 720 - $uc720 $valyuta",'callback_data'=>"xizm-720uc-PUBGMOBILE-UC"]],[['text'=>"🔵 985 - $uc985 $valyuta",'callback_data'=>"xizm-985uc-PUBGMOBILE-UC"]],[['text'=>"🔵 1320 - $uc1320 $valyuta",'callback_data'=>"xizm-1320uc-PUBGMOBILE-UC"]],[['text'=>"🔵 1800 - $uc1800 $valyuta",'callback_data'=>"xizm-1800uc-PUBGMOBILE-UC"]],[['text'=>"🔵 2125 - $uc2125 $valyuta",'callback_data'=>"xizm-2125uc-PUBGMOBILE-UC"]],[['text'=>"🔵 2460 - $uc2460 $valyuta",'callback_data'=>"xizm-2460uc-PUBGMOBILE-UC"]],[['text'=>"🔵 3950 - $uc3950 $valyuta",'callback_data'=>"xizm-3950uc-PUBGMOBILE-UC"]],[['text'=>"🔵 8100 - $uc8100 $valyuta",'callback_data'=>"xizm-8100uc-PUBGMOBILE-UC"]] ]])]); }
if($data=="fire"){ bot('editMessageText',['chat_id'=>$cid2,'message_id'=>$mid2,'text'=>"<b>🔴 FREE FIRE ALMAZ bo'limiga hush kelibsiz!</b>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"100 💎 = $almaz100 $valyuta",'callback_data'=>"xizm-100almaz-FreeFire-Almaz"]],[['text'=>"210 💎 = $almaz210 $valyuta",'callback_data'=>"xizm-210almaz-FreeFire-Almaz"]],[['text'=>"530 💎 = $almaz530 $valyuta",'callback_data'=>"xizm-530almaz-FreeFire-Almaz"]],[['text'=>"1080 💎 = $almaz1080 $valyuta",'callback_data'=>"xizm-1080almaz-FreeFire-Almaz"]],[['text'=>"2200 💎 = $almaz2200 $valyuta",'callback_data'=>"xizm-2200almaz-FreeFire-Almaz"]] ]])]); }
if(mb_stripos($data,"xizm-")!==false){ $xiz=explode("-",$data)[1]; $ich=explode("-",$data)[2]; $val=explode("-",$data)[3]; $donnarx=file_get_contents("donat/$ich/$xiz.txt"); bot('editMessageText',['chat_id'=>$cid2,'message_id'=>$mid2,'text'=>"📦 <b>Donat tanlandi:</b>\n\n💵 <b>Miqdori:</b> $xiz\n💸 <b>Narxi:</b> $donnarx $valyuta\n\n📑 <i>Donat $ich ID orqali amalga oshiriladi.</i>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"✅ Tanlash",'callback_data'=>"tanla-$xiz-$ich-$val"]], [['text'=>"◀️ Orqaga",'callback_data'=>"ucpubg"]] ]])]); }
if(mb_stripos($data,"tanla-")!==false){ $ex=explode("-",$data); $xiz=$ex[1]; $ich=$ex[2]; $val=$ex[3]; $kabinet=db_fetch("SELECT * FROM users WHERE id = '$cid2'"); $donnarx=file_get_contents("donat/$ich/$xiz.txt"); $yetmadi=$donnarx-$kabinet['balance']; if($kabinet['balance']>=$donnarx){ bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); bot('SendMessage',['chat_id'=>$cid2,'text'=>"<b><u>Botga $ich ID raqamingizni yuboring:</u></b>",'parse_mode'=>'html','reply_markup'=>$ort]); file_put_contents("user/$chat_id.step","next-$xiz-$ich-$val"); exit(); }else{ bot('SendMessage',['chat_id'=>$cid2,'text'=>"<b>🤷‍♂ Hisobingizga $yetmadi so'm yetishmadi!</b>",'parse_mode'=>'html']); exit(); } }
if(mb_stripos($step,"next-")!==false){ $ex=explode("-",$step); $xiz=$ex[1]; $ich=$ex[2]; $val=$ex[3]; $rew13=db_fetch("SELECT * FROM users WHERE id = '$cid'"); $pul13=$rew13['balance']; bot('SendMessage',['chat_id'=>$cid,'text'=>"<b>⛔ Donatni tasdiqlashdan oldin tekshiring:\n\n🎮 O'yin:</b> <i>$ich $val</i>\n💳 <b>Donat miqdori:</b> <i>$xiz</i>\n💵 <b>Balansingiz:</b> <i>$pul13 $valyuta</i>\n🆔 <b>$ich ID:</b> <code>$text</code>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"✅ Tasdiqlash",'callback_data'=>"tasdiq-$ich-$xiz-$val-$text"]], [['text'=>"🚫 Bekor qilish",'callback_data'=>"bekor"]] ]])]); @unlink("user/$cid.step"); exit(); }
if($data=="bekor"){ bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); bot('SendMessage',['chat_id'=>$cid2,'text'=>"<b>⛔️ Bekor qilindi!</b>",'parse_mode'=>'html','reply_markup'=>$menu]); exit(); }
if(mb_stripos($data,"tasdiq-")!==false){ $ex=explode("-",$data); $ich=$ex[1]; $xiz=$ex[2]; $val=$ex[3]; $ids=$ex[4]; $rew13=db_fetch("SELECT * FROM users WHERE id = '$cid2'"); $narxi=file_get_contents("donat/$ich/$xiz.txt"); $ayir=$rew13['balance']-$narxi; db_exec("UPDATE users SET balance='$ayir' WHERE id='$cid2'"); bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); bot('SendMessage',['chat_id'=>$cid2,'text'=>"<b>✅ So'rovingiz adminga yuborildi.\n\n$ich ID:</b> <code>$ids</code>",'parse_mode'=>'html','reply_markup'=>$menu]); bot('SendMessage',['chat_id'=>$admin,'text'=>"<b>✅ Yangi donat.\n\n👤 Egasi:</b> <i><a href='tg://user?id=$cid2'>$cid2</a></i>\n🎮 <b>O'yin:</b> <i>$ich $val</i>\n💳 <b>Miqdor:</b> <i>$xiz</i>\n🆔 <b>ID:</b> <code>$ids</code>",'parse_mode'=>'html','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"✅ Tasdiqlash",'callback_data'=>"donaton-$ich-$xiz-$val-$ids-$cid2"]], [['text'=>"🚫 Bekor qilish",'callback_data'=>"bekor"]] ]])]); exit(); }
if(mb_stripos($data,"donaton-")!==false){ $ex=explode("-",$data); $ich=$ex[1]; $xiz=$ex[2]; $val=$ex[3]; $ids=$ex[4]; $donatchi=$ex[5]; bot('SendMessage',['chat_id'=>$donatchi,'text'=>"<b>✅ So'rovingiz qabul qilindi.\n\nℹ️ $ich $val hisobingizga $xiz tushurildi.</b>",'parse_mode'=>'html','reply_markup'=>$menu]); bot('SendMessage',['chat_id'=>$admin,'text'=>"<b>✅ Donat qabul qilindi.\n\n👤 Egasi:</b> <i><a href='tg://user?id=$donatchi'>$donatchi</a></i>",'parse_mode'=>'html','reply_markup'=>$menu]); }

// ─── BUYURTMA HOLATI ──────────────────────────────────────────────
if($text=="🛒 𝔹𝕦𝕪𝕦𝕣𝕥𝕞𝕒 𝕩𝕠𝕝𝕒𝕥𝕚" || $text=="/order" and joinchat($cid)==1){
    $rew14=db_fetch("SELECT * FROM myorder WHERE user_id = '$cid'");
    if(!$rew14){ sms($cid,"❗️Sizda faol buyurtmalar yo'q.",json_encode(['inline_keyboard'=>[[['text'=>"🔎 Izlab topish",'callback_data'=>"bytopish"]]]])); }
    else{ $orders14=db_fetchall("SELECT * FROM myorder WHERE user_id = '$cid'"); $k=[]; foreach($orders14 as $my14) $k[]=["text"=>$my14['order_id'],"callback_data"=>"idby-".$my14['order_id']]; $keysboard2=array_chunk($k,4); $keysboard2[]=[['text'=>"🔎 Buyurtma ma'lumoti","callback_data"=>"bytopish"]]; sms($cid,"🛍️ Barcha buyurtmalaringiz!",json_encode(['inline_keyboard'=>$keysboard2])); }
}
if(mb_stripos($data,"idby-")!==false){ $ex=explode("-",$data); $text15=$ex[1]; $rew15=db_fetch("SELECT * FROM orders WHERE order_id = '$text15'"); $ori=$rew15['api_order']; $prov=$rew15['provider']; $ap=db_fetch("SELECT * FROM providers WHERE id = '$prov'"); $ourl=$ap['api_url']; $okey=$ap['api_key']; $s=json_decode(get($ourl."?key=$okey&action=status&order=$ori"),1); $son=$s['remains']; $response=$rew15['status']; if($response=="Completed")$status="✅ Bajarilgan"; elseif($response=="In progress")$status="♻️ Jarayonda"; elseif($response=="Partial")$status="⭕ Qisman bajarilgan"; elseif($response=="Pending")$status="⏰ Kutilmoqda"; elseif($response=="Processing")$status="🔁 Qayta ishlanmoqda"; elseif($response=="Canceled")$status="❌ Bekor qilingan"; if(!$rew15 or ($s['error']??false)){ sms($cid,"❌ Buyurtma topilmadi!",$m); }else{ del(); sms($cid2,"<b>✅ Buyurtma topildi!</b>\n\n<b>📯 Holati:</b> $status\n<b>🔎 Qoldiq:</b> $son ta",null); } }

// ─── NOMER OLISH ─────────────────────────────────────────────────
if($text=="📞 ℕ𝕠𝕞𝕖𝕣 𝕠𝕝𝕚𝕤𝕙"){ bot('sendMessage',['chat_id'=>$cid,'text'=>"❗️Bo'limdan foydalanish shartlari:\n\n- Virtual nomer berilganda almashtirishingiz mumkin\n- SMS kod kelsa nomer almashtirilmaydi va pul yechiladi\n- Telegram uchun nomer olsangiz va kod telegram orqali kelsa darhol bekor qiling!\n\n☝️ Yuqoridagi holatlar uchun da'volar qabul qilinmaydi",'parse_mode'=>"html",'reply_markup'=>json_encode(['remove_keyboard'=>true,'inline_keyboard'=>[[['text'=>"✅ Roziman",'callback_data'=>"hop"]],[['text'=>"❌ Bekor qilish",'callback_data'=>"menu_tolov"]]]])]); }
if($data=="hop"){ $url15=json_decode(file_get_contents("https://api.sms-activate.org/stubs/handler_api.php?api_key=$simkey&action=getCountries"),true); $urla15=file_get_contents("https://api.sms-activate.org/stubs/handler_api.php?api_key=$simkey&action=getCountries"); if($urla15=="BAD_KEY" or $urla15=="NO_KEY"){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"⚠️ Botga API kalit ulanmagan!",'show_alert'=>true]); }else{ $key=[]; $countries=["Russia"=>"🇷🇺 Rossiya","Ukraine"=>"🇺🇦 Ukraina","Kazakhstan"=>"🇰🇿 Qozog'iston","China"=>"🇨🇳 Xitoy","Philippines"=>"🇵🇭 Filippin","Myanmar"=>"🇲🇲 Myanma","Indonesia"=>"🇮🇩 Indoneziya","Malaysia"=>"🇲🇾 Malayziya","Kenya"=>"🇰🇪 Keniya","Tanzania"=>"🇹🇿 Tanzaniya"]; for($i=0;$i<10;$i++){ $eng=$url15["$i"]['eng']; $n=$countries[$eng]??$eng; $id15=$url15["$i"]['id']; $key[]=["text"=>"$n",'callback_data'=>"raqam=tg=ig=fb=tw=vi=oi=ts=go=$id15=$n"]; } $key1=array_chunk($key,2); $key1[]=[["text"=>"1/6","callback_data"=>"null"],['text'=>"⏭️",'callback_data'=>"davlat2"]]; $key1[]=[['text'=>"⏮️ Orqaga","callback_data"=>"orqa"]]; bot('EditMessageText',['chat_id'=>$cid2,'message_id'=>$mid2,'text'=>"*Nomer olish uchun davlatlar:*",'parse_mode'=>'markdown','reply_markup'=>json_encode(['inline_keyboard'=>$key1])]); } }
if(stripos($data,"olish=")!==false){ $xiz15=explode("=",$data)[1]; $id15=explode("=",$data)[2]; $op15=explode("=",$data)[3]; $pric15=explode("=",$data)[4]; $davlat15=explode("=",$data)[5]; $row15=db_fetch("SELECT * FROM users WHERE id = '$cid2'"); $foyid15=$row15['user_id']; if($row15['balance']>=$pric15){ $arrContextOptions=["ssl"=>["verify_peer"=>false,"verify_peer_name"=>false]]; $response15=file_get_contents("https://api.sms-activate.org/stubs/handler_api.php?api_key=$simkey&action=getNumber&service=$xiz15&country=$id15&operator=$op15",false,stream_context_create($arrContextOptions)); $pieces15=explode(":",$response15); $simid15=$pieces15[1]; $phone15=$pieces15[2]; if($response15=="NO_NUMBERS"){ $msgs15="❌ Bu tarmoq uchun nomer yo'q!"; } elseif($response15=="NO_BALANCE"){ $msgs15="⚠️ Xatolik!"; } if($response15=="NO_NUMBERS" or $response15=="NO_BALANCE"){ bot("answerCallbackQuery",["callback_query_id"=>$update->callback_query->id,'text'=>$msgs15,"show_alert"=>true]); } elseif(mb_stripos($response15,"ACCESS_NUMBER")!==false){ $miqdor15=$row15['balance']-$pric15; db_exec("UPDATE users SET balance=$miqdor15 WHERE id='$cid2'"); bot('editmessagetext',['chat_id'=>$cid2,'message_id'=>$mid2,'text'=>"\n🛎 *Sizga nomer berildi\n🌍 Davlat: $davlat15\n💸 Narxi: $pric15 so'm\n📞 Nomeringiz: +$phone15\n\nNusxalash:* `$phone15`\n\n*📨 Kodni olish uchun « 📩 SMS-kod olish » tugmasini bosing!*",'parse_mode'=>'markdown','reply_markup'=>json_encode(['inline_keyboard'=>[ [['text'=>"📩 SMS-kod olish",'callback_data'=>"pcode_".$simid15."_".$pric15]], [['text'=>"❌ Bekor qilish",'callback_data'=>"otmena_".$simid15."_".$pric15]] ]])]); bot('sendMessage',['chat_id'=>$proof,'text'=>"📞 Yangi nomer: <code>+$phone15</code>\n💰 Narxi: $pric15 so'm\n👤 Buyurtmachi: $foyid15",'parse_mode'=>'html']); } }else{ bot("answerCallbackQuery",["callback_query_id"=>$update->callback_query->id,'text'=>"❗Sizda mablag' yetarli emas!","show_alert"=>true]); } }
if(stripos($data,"pcode_")!==false){ $ex=explode("_",$data); $simid16=$ex[1]; $so16=$ex[2]; $sims=@file_get_contents("simcard.txt"); if(mb_stripos($sims,$simid16)!==false){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"❌ Kech qoldingiz!",'show_alert'=>true]); exit(); }else{ $response16=file_get_contents("https://api.sms-activate.org/stubs/handler_api.php?api_key=$simkey&action=getStatus&id=$simid16"); if(mb_stripos($response16,"STATUS_OK")!==false){ $pieces16=explode(":",$response16); $smskod=$pieces16[1]; bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); bot('sendMessage',['chat_id'=>$cid2,'text'=>"📩 *SMS keldi!\n\n🔢 KOD:* `$smskod`",'parse_mode'=>'markdown']); }elseif($response16=="STATUS_CANCEL"){ bot("answerCallbackQuery",["callback_query_id"=>$update->callback_query->id,'text'=>"✅ Balansingizga $so16 so'm qaytarildi!","show_alert"=>true]); $row16=db_fetch("SELECT * FROM users WHERE id = '$cid2'"); $miqdor16=$so16+$row16['balance']; db_exec("UPDATE users SET balance=$miqdor16 WHERE id='$cid2'"); file_put_contents("simcard.txt","\n".$simid16,FILE_APPEND); }else{ bot("answerCallbackQuery",["callback_query_id"=>$update->callback_query->id,'text'=>"⏰ SMS kutilmoqda!","show_alert"=>true]); } } }
if(stripos($data,"otmena_")!==false){ $simid16=explode("_",$data)[1]; $so16=explode("_",$data)[2]; $sims=@file_get_contents("simcard.txt"); $response16=file_get_contents("https://api.sms-activate.org/stubs/handler_api.php?api_key=$simkey&action=setStatus&status=8&id=$simid16"); if(mb_stripos($sims,$simid16)!==false){ bot('answerCallbackQuery',['callback_query_id'=>$qid,'text'=>"❌ Kech qoldingiz!",'show_alert'=>true]); exit(); }else{ if(mb_stripos($response16,"ACCESS_CANCEL")!==false){ bot("answerCallbackQuery",["callback_query_id"=>$update->callback_query->id,'text'=>"✅ Balansingizga $so16 so'm qaytarildi","show_alert"=>true]); $row16=db_fetch("SELECT * FROM users WHERE id = '$cid2'"); $miqdor16=$so16+$row16['balance']; db_exec("UPDATE users SET balance=$miqdor16 WHERE id='$cid2'"); file_put_contents("simcard.txt","\n".$simid16,FILE_APPEND); }else{ bot("answerCallbackQuery",["callback_query_id"=>$update->callback_query->id,'text'=>"❗ Kuting....","show_alert"=>true]); } } }

// ─── TARIF ───────────────────────────────────────────────────────
if($text=="/tarif"){ sms($cid,"👉 Barcha ta'riflar",keyboard([[['text'=>"📝 Ta'riflar",'url'=>"https://".$_SERVER['HTTP_HOST']."/services"]]])); }

// ─── ORDERED ─────────────────────────────────────────────────────
if(stripos($data,"ordered=")!==false){ $n=explode("=",$data)[1]; $n2=explode("=",$data)[2]; $s=db_fetch("SELECT * FROM services WHERE service_id= '$n'"); if($s){ $nam=base64_decode($s['service_name']); $sid=$s['service_id']; $narx=$s['service_price']; $curr=$s['api_currency']; $ab=$s['service_desc']?$s['service_desc']:null; $api=$s['api_service']; $type=$s['service_type']; $spi=$s['service_api']; $min=$s["service_min"]; $max=$s["service_max"]; $ap=db_fetch("SELECT * FROM providers WHERE id = $api"); $surl=$ap['api_url']; $skey=$ap['api_key']; if($curr=="USD")$fr=get("set/usd"); elseif($curr=="RUB")$fr=get("set/rub"); elseif($curr=="INR")$fr=get("set/inr"); elseif($curr=="TRY")$fr=get("set/try"); else $fr=1; $abs=$ab?"\n".base64_decode($ab)."":null; if($type=="Default" or $type=="default") $abdesc="🔽 Minimal: $min ta\n🔼 Maksimal: $max ta\n\n$abs"; else $abdesc=$abs; if(empty($min) or empty($max)){ bot('answerCallbackQuery',['callback_query_id'=>$update->callback_query->id,'text'=>"⚠️ Xato ketdi, qaytadan urining.",'show_alert'=>true]); }else{ edit($chat_id,$message_id,"\n<b>$nam</b>\n\n🔑 Xizmat IDsi: <code>$sid</code>\n💵 Narxi (1000 ta) - $narx so'm\n\n$abdesc\n\n",json_encode(['inline_keyboard'=>[ [['text'=>"✅ Tanlash",'callback_data'=>"order=$spi=$min=$max=".$narx."=$type=".$api."=$sid"]], [['text'=>"⏪ Orqaga",'callback_data'=>"tanla2=$n2"]] ]])); exit; } } }
if(stripos($data,"order=")!==false){ $oid=explode("=",$data)[1]; $omin=explode("=",$data)[2]; $omax=explode("=",$data)[3]; $orate=explode("=",$data)[4]; $otype=explode("=",$data)[5]; $prov=explode("=",$data)[6]; $serv=explode("=",$data)[7]; if($otype=="Default" or $otype=="default"){ del(); sms($chat_id,"⬇️ Kerakli buyurtma miqdorini kiriting:",$ort); put("user/$chat_id.step","order=default=sp1"); put("user/$chat_id.params","$oid=$omin=$omax=$orate=$prov=$serv"); put("user/$chat_id.si",$oid); exit; }elseif($otype=="Package"){ del(); sms($chat_id,"📎 Kerakli havolani kiriting (https://):",$ort); put("user/$chat_id.step","order=package=sp2=1=$orate"); put("user/$chat_id.params","$oid=$omin=$omax=$orate=$prov=$serv"); put("user/$chat_id.si",$oid); exit; } }
$s17=explode("=",$step);
if($s17[0]=="order" and $s17[1]=="default" and $s17[2]=="sp1" and is_numeric($text) and joinchat($cid)==1){ $p17=explode("=",get("user/$cid.params")); $narxi17=$p17[3]/1000*$text; if($text>=$p17[1] and $text<=$p17[2]){ $rew17=db_fetch("SELECT * FROM users WHERE id = '$cid'"); if($rew17['balance']>=$narxi17){ sms($cid,"\n🛍️ $text saqlandi, havolani yuboring.\n\n⚠️ Sahifangiz ochiq bo'lishi kerak!",$ort); put("user/$cid.step","order=$s17[1]=sp2=$text=$narxi17"); put("user/$cid.qu",$text); exit; }else{ sms($cid,"❌ Yetarli mablag' yo'q\n💰 Narxi: $narxi17 so'm\n\nBoshqa miqdor kiriting:",null); exit; } }else{ sms($cid,"\n⚠️ Noto'g'ri miqdor\n\n⬇️ Minimal: $p17[1]\n⬆️ Maksimal: $p17[2]\n\nBoshqa miqdor kiriting",null); exit; } }
if(($s17[0]=="order" and ($s17[1]=="default" or $s17[1]=="package") and $s17[2]=="sp2" and joinchat($cid)==1)){ if($s17[1]=="default") $pc17="🔢 Buyurtma miqdori: $s17[3] ta"; $rew17=db_fetch("SELECT * FROM users WHERE id = '$cid'"); if($rew17['balance']>=$s17[4]){ if((mb_stripos($text,"https://")!==false) or (mb_stripos($text,"@")!==false)){ sms($cid,"\n➡️ Malumotlarni tekshiring:\n\n💵 Buyurtma narxi: $s17[4] so'm\n📎 Manzil: $text\n$pc17\n\n⚠️ To'g'ri bo'lsa (✅ Tasdiqlash) tugmasini bosing",json_encode(['inline_keyboard'=>[[['text'=>"✅ Tasdiqlash",'callback_data'=>"checkorder=".uniqid()]]]])); put("user/$cid.step","order=$s17[1]=sp3=$s17[3]=$s17[4]=$text"); put("user/$cid.ur",$text); exit; }else{ sms($cid,"⚠️ Havola noto'g'ri\nQaytadan harakat qiling",null); } }else{ sms($cid,"❌ Yetarli mablag' yo'q",$ort); } }
$sc17=explode("=",get("user/$chat_id.step"));
if(stripos($data,"checkorder=")!==false and $sc17[0]=="order" and ($sc17[1]=="default" or $sc17[1]=="package") and $sc17[2]=="sp3" and joinchat($chat_id)==1){ $rew17=db_fetch("SELECT * FROM users WHERE id = '$chat_id'"); if($rew17['balance']>=$sc17[4]){ $sp17=explode("=",get("user/$chat_id.params")); $mprovider=db_fetch("SELECT * FROM providers WHERE id = ".$sp17[4]); $surl=$mprovider['api_url']; $skey=$mprovider['api_key']; $j17=json_decode(get($surl."?key=$skey&action=add&service=".get("user/$chat_id.si")."&link=".get("user/$chat_id.ur")."&quantity=".get("user/$chat_id.qu")),1); $jid17=$j17['order']; if(empty($jid17)){ bot('answerCallbackQuery',['callback_query_id'=>$cqid,'text'=>"⚠️ Xatolik yuz berdi, keyinroq urining",'show_alert'=>1]); sms($chat_id,"🖥️ Asosiy menyudasiz",$menu); @unlink("user/$chat_id.step"); @unlink("user/$chat_id.params"); exit; }else{ $oe=db_count("SELECT * FROM orders"); $or=$oe+1; $sav=date("Y.m.d H:i:s"); db_exec("INSERT INTO myorder(order_id,user_id,retail,status,service,order_create,last_check) VALUES ('$or','$chat_id','$sc17[4]','Pending','$sp17[5]','$sav','$sav')"); db_exec("INSERT INTO orders(api_order,order_id,provider,status) VALUES ('$jid17','$or','$sp17[4]','Pending')"); $order17=str_replace(["{order}","{order_api}"],["$or","$jid17"],enc("decode",$setting['orders'])); sms($chat_id,$order17,null); $miqdor17=$rew17['balance']-$sc17[4]; db_exec("UPDATE users SET balance=$miqdor17 WHERE id='$chat_id'"); @unlink("user/$chat_id.step"); del(); exit; } } }

// ─── FOYDALANUVCHI QO'SHISH ──────────────────────────────────────
if($message){ adduser($cid); }

// ─── MAIN ────────────────────────────────────────────────────────
if(($data=="main") and (joinchat($cid2)==1)){ bot('AnswerCallbackQuery',['callback_query_id'=>$qid,'text'=>"✅ Asosiy menyudasiz!",'show_alert'=>false]); bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); bot('sendmessage',['chat_id'=>$cid2,'parse_mode'=>"html",'reply_markup'=>$m,'text'=>"🖥️ <b>Asosiy menyuga qaytdingiz.</b>"]); @unlink("user/$cid2.step"); @unlink("user/$cid2.ur"); @unlink("user/$cid2.params"); @unlink("user/$cid2.qu"); @unlink("user/$cid2.si"); exit(); }

// ─── YOPISH ──────────────────────────────────────────────────────
if($data=="yopish"){ bot('deleteMessage',['chat_id'=>$cid2,'message_id'=>$mid2]); }

?>
