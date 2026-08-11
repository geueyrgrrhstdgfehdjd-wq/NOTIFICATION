

// ==========================================
// [ ⚠️ BY : DON'T MONEY ]
// ==========================================

const { 
    Client, GatewayIntentBits, SlashCommandBuilder, REST, Routes, 
    EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, StringSelectMenuBuilder, 
    ChannelType, PermissionFlagsBits 
} = require('discord.js');
const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');
const https = require('https');

// ==========================================
// [ ตั้งค่าเริ่มต้น ]
// ==========================================
// แนะนำให้ไปรีเซ็ต Token ใหม่ในเว็บ Discord แล้วค่อยเอามาใส่ ห้ามมีช่องว่างเด็ดขาด
const TOKEN = 'MTUzNjczMzk4ODEzNDA2NDE1MQ.GIEz2s.pirBib6r_EODxFbpW__UQhp_4oB2j8jDLqTcyg'; 
const CLIENT_ID = '1536733988134064151';
const ALLOWED_GUILD_ID = '1504934379775070338'; 
const ADMIN_ID = '1504934379775070338'; 
const LOG_CHANNEL_ID = '1536765306028957716'; // <--- เพิ่มไอดีช่องแจ้งเตือนตรงนี้

// ==========================================
// [ คลังเก็บอิโมจิ ]
// ==========================================
const emojis = {
    wingL: '<a:leftwing:1462740622896271362>',
    wingR: '<a:rightwing:1462740682899722343>',
    loading: '<a:dapex_loader:1460969116469825577>',
    success: '<a:Done:1482674401701793853>',
    error: '<a:6443softbankexclamation:1462341527060746292>',
    host: '<a:botsever48:1461894763539202119>',
    cart: '<a:cart:1461894728143470724>',
    box: '<a:dbnormiebox:1461894755842523364>',
    premium: '<a:Nitro:1461894771034423399>',
    free: '<a:gift_bunnystore:1461894543380320329>',
    play: '<a:dapex_online:1460969132307517563>',
    stop: '<:dapex_stop:1460969474617380929>',
    restart: '<a:green_cycle:1461894522098155570>',
    clear: '<a:3907softbankfire:1461894550200127703>',
    money: '<a:8235_money:1482674394097647716>',
    arrow: '<:dapex_arrow:1460969484407013533>',
    node: '<a:botsever48:1461894763539202119>',
    python: '<a:67573sushiroll:1461894642608902299>'
};

// ==========================================
// [ ตัวแปรเก็บข้อมูล (Memory State) ]
// ==========================================
const userLanguage = new Map(); 
const premiumUsers = new Map(); 
const runningProcesses = new Map(); 
const processLogs = new Map(); 

const HOST_DIR = path.join(__dirname, 'hostbot');
if (!fs.existsSync(HOST_DIR)) fs.mkdirSync(HOST_DIR, { recursive: true });

const client = new Client({
    intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent]
});

// ==========================================
// [ ฟังก์ชัน ระบบแจ้งเตือน Log ]
// ==========================================
async function sendSystemLog(user, plan, lang, isSuccess) {
    try {
        const logChannel = client.channels.cache.get(LOG_CHANNEL_ID);
        if (!logChannel) return;

        const statusEmoji = isSuccess ? emojis.success : emojis.error;
        const langEmoji = lang === 'nodejs' ? emojis.node : emojis.python;
        const planEmoji = plan === 'premium' ? emojis.premium : emojis.free;

        const embed = new EmbedBuilder()
            .setTitle(`${emojis.host} บันทึกการอัปโหลดไฟล์`)
            .setDescription(`${emojis.arrow} **ผู้ใช้:** ${user}\n${emojis.arrow} **สถานะ:** ${statusEmoji}\n${emojis.arrow} **แพ็กเกจ:** **${plan.toUpperCase()}** ${planEmoji}\n${emojis.arrow} **ภาษา:** **${lang.toUpperCase()}** ${langEmoji}`)
            .setColor(isSuccess ? '#2b2d31' : '#ed4245')
            .setTimestamp();

        await logChannel.send({ embeds: [embed] });
    } catch (error) {
        console.error('ไม่สามารถส่ง Log ได้:', error);
    }
}

// ==========================================
// [ ฟังก์ชัน Auto-Install Modules ]
// ==========================================
function autoInstallModules(filePath, lang, userDir) {
    try {
        const code = fs.readFileSync(filePath, 'utf8');
        const modules = new Set();

        if (lang === 'nodejs') {
            const reqRegex = /require\(['"]([^'"]+)['"]\)/g;
            let match;
            const builtIns = ['fs', 'path', 'crypto', 'http', 'https', 'events', 'util', 'child_process', 'os', 'stream'];
            while ((match = reqRegex.exec(code)) !== null) {
                const mod = match[1].split('/')[0];
                if (!builtIns.includes(mod) && !mod.startsWith('.')) modules.add(mod);
            }
            if (modules.size > 0) {
                const modStr = Array.from(modules).join(' ');
                console.log(`[Auto-Install] Installing NPM packages: ${modStr}`);
                execSync(`npm install ${modStr}`, { cwd: userDir, stdio: 'ignore' });
            }
        } else if (lang === 'python') {
            const impRegex = /^(?:from\s+([a-zA-Z0-9_]+).*|import\s+([a-zA-Z0-9_,\s]+))/gm;
            let match;
            while ((match = impRegex.exec(code)) !== null) {
                const modStr = match[1] || match[2];
                if (modStr) {
                    modStr.split(',').forEach(m => {
                        const cleanMod = m.trim().split(/\s+/)[0];
                        if (cleanMod) modules.add(cleanMod);
                    });
                }
            }
            if (modules.size > 0) {
                const modStr = Array.from(modules).join(' ');
                console.log(`[Auto-Install] Installing PIP packages: ${modStr}`);
                execSync(`pip install ${modStr}`, { cwd: userDir, stdio: 'ignore' });
            }
        }
        return true;
    } catch (err) {
        console.error(err);
        return false;
    }
}

// ==========================================
// [ ระบบเริ่มต้น & Slash Commands ]
// ==========================================
client.once('ready', async () => {
    console.log(`${emojis.success} ล็อกอินเข้าสู่ระบบในชื่อ ${client.user.tag}`);
    
    const commands = [
        new SlashCommandBuilder().setName('host-bot').setDescription('เปิดเมนูสำหรับเช่า Host Bot'),
        new SlashCommandBuilder()
            .setName('add-prm')
            .setDescription('เพิ่มพรีเมียมให้ผู้ใช้ (เฉพาะแอดมิน)')
            .addUserOption(option => option.setName('user').setDescription('ระบุผู้ใช้').setRequired(true))
            .addIntegerOption(option => option.setName('days').setDescription('จำนวนวัน').setRequired(true))
    ].map(command => command.toJSON());

    const rest = new REST({ version: '10' }).setToken(TOKEN);
    try {
        await rest.put(Routes.applicationGuildCommands(CLIENT_ID, ALLOWED_GUILD_ID), { body: commands });
    } catch (error) { console.error(error); }
});

// ==========================================
// [ ระบบจัดการ Interactions ]
// ==========================================
client.on('interactionCreate', async interaction => {
    if (interaction.guild && interaction.guild.id !== ALLOWED_GUILD_ID) {
        if (interaction.isRepliable()) return interaction.reply({ content: `${emojis.error} คำสั่งนี้ไม่สามารถใช้ในเซิร์ฟเวอร์นี้ได้!`, ephemeral: true });
        return;
    }

    if (interaction.isChatInputCommand()) {
        if (interaction.commandName === 'host-bot') {
            await interaction.reply({ content: `${emojis.loading} กำลังสร้างเมนู...`, ephemeral: true });

            const embed = new EmbedBuilder()
                .setTitle(`${emojis.wingL} ${emojis.host} ระบบ Host Bot อัตโนมัติ ${emojis.wingR}`)
                .setDescription(`\`\`\`\nกรุณาเลือกภาษาที่ต้องการรันด้านล่าง\nจากนั้นกดปุ่ม "เช่าโฮสต์" หรือจัดการโค้ดของคุณ\n\`\`\``)
                .setColor('#2b2d31')
                .setImage('https://i.imgur.com/AfFp7pu.png');

            const langDropdown = new ActionRowBuilder().addComponents(
                new StringSelectMenuBuilder()
                    .setCustomId('select_lang')
                    .setPlaceholder('>>> ภาษาที่รองรับ <<<')
                    .addOptions(
                        { label: 'Node.js', value: 'nodejs', emoji: '1461894763539202119' },
                        { label: 'Python', value: 'python', emoji: '1461894642608902299' },
                        { label: '>>> ล้างตัวเลือก <<<', value: 'clear', emoji: '1461894550200127703' }
                    )
            );

            const buttons = new ActionRowBuilder().addComponents(
                new ButtonBuilder().setCustomId('btn_host').setLabel('เช่าโฮสต์').setEmoji('1461894728143470724').setStyle(ButtonStyle.Success),
                new ButtonBuilder().setCustomId('btn_console').setLabel('เช็คคอนโซล').setEmoji('1461894763539202119').setStyle(ButtonStyle.Secondary)
            );

            await interaction.channel.send({ embeds: [embed], components: [langDropdown, buttons] });
        }

        if (interaction.commandName === 'add-prm') {
            if (interaction.user.id !== ADMIN_ID) return interaction.reply({ content: `${emojis.error} เฉพาะแอดมินเท่านั้น!`, ephemeral: true });
            
            const targetUser = interaction.options.getUser('user');
            const days = interaction.options.getInteger('days');
            premiumUsers.set(targetUser.id, Date.now() + (days * 24 * 60 * 60 * 1000));
            await interaction.reply({ content: `${emojis.success} เพิ่มพรีเมียม ${emojis.premium} ให้ ${targetUser} จำนวน ${days} วันเรียบร้อย`, ephemeral: true });
        }
    }

    if (interaction.isStringSelectMenu()) {
        if (interaction.customId === 'select_lang') {
            const selected = interaction.values[0];
            if (selected === 'clear') {
                userLanguage.delete(interaction.user.id);
                return interaction.reply({ content: `${emojis.clear} ล้างตัวเลือกภาษาเรียบร้อยแล้ว`, ephemeral: true });
            } else {
                userLanguage.set(interaction.user.id, selected);
                return interaction.deferUpdate();
            }
        }

        if (interaction.customId === 'select_package') {
            const plan = interaction.values[0];
            if (plan === 'premium') {
                const expire = premiumUsers.get(interaction.user.id);
                if (!expire || expire < Date.now()) {
                    return interaction.reply({ content: `${emojis.error} คุณไม่มีสิทธิ์ใช้งาน Premium ${emojis.premium}\n(ต้องผ่านการแอดจากแอดมินเท่านั้น)`, ephemeral: true });
                }
            }

            const lang = userLanguage.get(interaction.user.id);
            await interaction.reply({ content: `${emojis.loading} กำลังสร้างช่องส่งไฟล์...`, ephemeral: true });

            const channel = await interaction.guild.channels.create({
                name: `host-${interaction.user.username}`,
                type: ChannelType.GuildText,
                permissionOverwrites: [
                    { id: interaction.guild.id, deny: [PermissionFlagsBits.ViewChannel] },
                    { id: interaction.user.id, allow: [PermissionFlagsBits.ViewChannel, PermissionFlagsBits.SendMessages, PermissionFlagsBits.AttachFiles] },
                    { id: client.user.id, allow: [PermissionFlagsBits.ViewChannel, PermissionFlagsBits.SendMessages, PermissionFlagsBits.AttachFiles] }
                ]
            });

            // แจ้งเตือนในแชทเดิมแบบ Ephemeral ว่าสร้างช่องสำเร็จแล้ว
            await interaction.editReply({ 
                content: null,
                embeds: [new EmbedBuilder().setColor('#2b2d31').setDescription(`${emojis.success} สร้างช่องสำเร็จ! ไปส่งไฟล์ที่ ${channel}`)] 
            });

            const targetExt = lang === 'nodejs' ? '.js' : '.py';
            await channel.send({
                content: `<@${interaction.user.id}>`,
                embeds: [
                    new EmbedBuilder()
                        .setTitle(`${emojis.box} ส่งไฟล์บอทของคุณที่นี่`)
                        .setDescription(`${emojis.arrow} แพ็กเกจ: **${plan.toUpperCase()}**\n${emojis.arrow} ภาษา: **${lang}**\n\n**ส่งไฟล์ \`${targetExt}\` ลงในช่องนี้** ${emojis.loading}\nบอทจะเช็คโมดูลและติดตั้งให้อัตโนมัติ (ช่องนี้จะถูกลบทิ้งเมื่อส่งไฟล์เสร็จสิ้น หรือหมดเวลาภายใน 5 นาที)`)
                        .setColor('#2b2d31')
                ]
            });

            const filter = m => m.author.id === interaction.user.id && m.attachments.size > 0;
            const collector = channel.createMessageCollector({ filter, time: 300000, max: 1 });

            collector.on('collect', async m => {
                const attachment = m.attachments.first();
                if (!attachment.name.endsWith(targetExt)) return m.reply(`${emojis.error} ต้องเป็นไฟล์ \`${targetExt}\` เท่านั้น!`);

                const userDir = path.join(HOST_DIR, interaction.user.id);
                if (!fs.existsSync(userDir)) fs.mkdirSync(userDir, { recursive: true });

                const filePath = path.join(userDir, attachment.name);
                const fileStream = fs.createWriteStream(filePath);

                const statusMsg = await channel.send(`${emojis.loading} กำลังดาวน์โหลดและตรวจสอบโค้ด...`);

                https.get(attachment.url, (response) => {
                    response.pipe(fileStream);
                    fileStream.on('finish', async () => {
                        fileStream.close();
                        
                        await statusMsg.edit(`${emojis.loading} ดึงไฟล์สำเร็จ! กำลังติดตั้ง Modules ที่จำเป็น (Auto-Install)...`);
                        const installSuccess = autoInstallModules(filePath, lang, userDir);
                        
                        // บันทึก Log การส่งไฟล์
                        await sendSystemLog(interaction.user, plan, lang, installSuccess);

                        if (installSuccess) {
                            await statusMsg.edit(`${emojis.success} บันทึกและติดตั้งโมดูลเข้า Host เรียบร้อย! กดปุ่ม **"เช็คคอนโซล"** ที่เมนูหลักเพื่อรันได้เลย\n\n${emojis.clear} *ช่องนี้จะถูกลบอัตโนมัติภายใน 15 วินาที*`);
                        } else {
                            await statusMsg.edit(`${emojis.error} เกิดข้อผิดพลาดในการติดตั้งโมดูล แต่บันทึกไฟล์สำเร็จแล้ว\n\n${emojis.clear} *ช่องนี้จะถูกลบอัตโนมัติภายใน 15 วินาที*`);
                        }

                        // ลบช่องหลังจากประมวลผลสำเร็จผ่านไป 15 วินาที
                        setTimeout(() => {
                            channel.delete().catch(() => {});
                        }, 15000);
                    });
                });
            });

            // ลบช่องอัตโนมัติหากไม่มีการส่งไฟล์ภายใน 5 นาที
            collector.on('end', (collected, reason) => {
                if (reason === 'time') {
                    channel.delete().catch(() => {});
                }
            });
        }
    }

    if (interaction.isButton()) {
        if (interaction.customId === 'btn_host') {
            const lang = userLanguage.get(interaction.user.id);
            if (!lang) return interaction.reply({ content: `${emojis.error} ต้องเลือกภาษาจาก dropdown ก่อน`, ephemeral: true });

            const packageDropdown = new ActionRowBuilder().addComponents(
                new StringSelectMenuBuilder()
                    .setCustomId('select_package')
                    .setPlaceholder('>>> เลือกแพ็กเกจ <<<')
                    .addOptions(
                        { label: 'Free', value: 'free', emoji: '1461894543380320329' },
                        { label: 'Premium [ 10 บาท/เดือน ]', value: 'premium', emoji: '1461894771034423399' }
                    )
            );

            await interaction.reply({ components: [packageDropdown], ephemeral: true });
        }

        if (interaction.customId === 'btn_console') sendConsole(interaction);

        if (interaction.customId === 'btn_restart') {
            stopProcess(interaction.user.id);
            startProcess(interaction.user.id, interaction);
        }

        if (interaction.customId === 'btn_stop') {
            stopProcess(interaction.user.id);
            processLogs.set(interaction.user.id, (processLogs.get(interaction.user.id) || '') + `\n[SYSTEM] ${emojis.stop} หยุดการทำงานแล้ว`);
            sendConsole(interaction, true);
        }
    }
});

// ==========================================
// [ ฟังก์ชันจัดการ Process & Console ]
// ==========================================
function startProcess(userId, interaction) {
    const userDir = path.join(HOST_DIR, userId);
    if (!fs.existsSync(userDir)) return interaction.reply({ content: `${emojis.error} ไม่พบไฟล์โปรเจกต์ ส่งไฟล์ก่อน!`, ephemeral: true });

    const files = fs.readdirSync(userDir).filter(f => f.endsWith('.js') || f.endsWith('.py'));
    if (files.length === 0) return interaction.reply({ content: `${emojis.error} ไม่พบไฟล์สคริปต์ในโฟลเดอร์`, ephemeral: true });
    
    const fileToRun = files[0];
    const filePath = path.join(userDir, fileToRun);
    const cmd = fileToRun.endsWith('.py') ? 'python' : 'node';

    processLogs.set(userId, `[SYSTEM] ${emojis.play} กำลังเริ่มรัน ${fileToRun}...\n`);
    
    const child = spawn(cmd, [fileToRun], { cwd: userDir });
    runningProcesses.set(userId, child);

    child.stdout.on('data', (data) => {
        let logs = processLogs.get(userId) || '';
        logs += data.toString();
        if (logs.length > 1500) logs = logs.slice(logs.length - 1500);
        processLogs.set(userId, logs);
    });

    child.stderr.on('data', (data) => {
        let logs = processLogs.get(userId) || '';
        logs += `[ERROR] ${data.toString()}`;
        if (logs.length > 1500) logs = logs.slice(logs.length - 1500);
        processLogs.set(userId, logs);
    });

    child.on('close', (code) => {
        let logs = processLogs.get(userId) || '';
        logs += `\n[SYSTEM] Process จบการทำงานด้วยรหัส ${code}`;
        processLogs.set(userId, logs);
        runningProcesses.delete(userId);
    });

    sendConsole(interaction, true);
}

function stopProcess(userId) {
    const child = runningProcesses.get(userId);
    if (child) {
        child.kill();
        runningProcesses.delete(userId);
    }
}

async function sendConsole(interaction, isUpdate = false) {
    const userId = interaction.user.id;
    let logs = processLogs.get(userId) || `[ ไม่มีข้อมูลคอนโซล ] ${emojis.loading}`;

    const embed = new EmbedBuilder()
        .setTitle(`${emojis.host} คอนโซลของ ${interaction.user.username}`)
        .setDescription(`\`\`\`\n${logs}\n\`\`\``)
        .setColor('#2b2d31');

    const buttons = new ActionRowBuilder().addComponents(
        new ButtonBuilder().setCustomId('btn_restart').setLabel('รีรัน').setEmoji('1461894522098155570').setStyle(ButtonStyle.Primary),
        new ButtonBuilder().setCustomId('btn_stop').setLabel('หยุดรัน').setEmoji('1460969474617380929').setStyle(ButtonStyle.Danger)
    );

    if (isUpdate) {
        await interaction.update({ embeds: [embed], components: [buttons] }).catch(() => interaction.reply({ embeds: [embed], components: [buttons], ephemeral: true }));
    } else {
        await interaction.reply({ embeds: [embed], components: [buttons], ephemeral: true });
    }
}

client.login(TOKEN);ait interaction.reply({ embeds: [embed], components: [buttons], ephemeral: true });
    }
}

client.login(TOKEN);
