const CLOUDINARY_URL = 'cloudinary://171272812288197:HEX6ayHSRPpjai6vC8oghdDFUEY@dk8aeedal';

function getCookies() {
    const cookies = {};
    document.cookie.split(';').forEach(cookie => {
        const [name, value] = cookie.split('=');
        cookies[name.trim()] = value.trim();
    });
    return cookies;
}

function setCookie(name, value, days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = "expires=" + date.toUTCString();
    document.cookie = name + "=" + value + ";" + expires + ";path=/";
}

function registerUser(username, password) {
    if (localStorage.getItem(username)) {
        alert('User already exists');
        return;
    }

    const user = {
        username: username,
        password: password,
        points: 1
    };

    localStorage.setItem(username, JSON.stringify(user));
    alert('User registered successfully');
    window.location.href = 'login.html';
}

function loginUser(username, password) {
    const user = JSON.parse(localStorage.getItem(username));

    if (!user || user.password !== password) {
        alert('Invalid username or password');
        return;
    }

    setCookie('user', username, 7);
    window.location.href = 'index.html';
}

function getUser() {
    const username = getCookies().user;
    if (!username) {
        return null;
    }

    return JSON.parse(localStorage.getItem(username));
}

function addTranslationButton() {
    const button = document.createElement('button');
    button.textContent = 'Translate';
    button.onclick = translatePage;
    document.body.appendChild(button);
}

function translatePage() {
    const userLang = navigator.language || navigator.userLanguage;
    let lang = 'en';
    if (userLang.includes('zh')) lang = 'zh';
    else if (userLang.includes('fr')) lang = 'fr';
    else if (userLang.includes('de')) lang = 'de';
    else if (userLang.includes('jp')) lang = 'jp';

    changeLanguage(lang);
}

function changeLanguage(lang) {
    const texts = {
        en: {
            heroText: 'IELTS Essay Correction Service, Improve Writing Quality.',
            heroButton: 'View services',
            aboutTitle: 'Expert essay correction',
            aboutText: 'Detailed essay evaluation and correction service focusing on four key areas: task completion, coherence and cohesion, vocabulary diversity, and grammar accuracy. We provide an overall score to help candidates understand their essay\'s overall level. Specific errors are highlighted with detailed improvement suggestions to enhance writing quality. Receive a thoroughly revised essay for comparison between the original and edited versions, clearly identifying areas for improvement.',
            contactButton: 'Get in touch',
            service1Title: 'Detailed Essay Evaluation',
            service1Text: 'Get in-depth feedback on your essay.',
            service1Button: 'Read more',
            service2Title: 'Grammar Correction',
            service2Text: 'Improve your grammar skills.',
            service2Button: 'Read more',
            service3Title: 'Vocabulary Enhancement',
            service3Text: 'Expand your vocabulary repertoire.',
            service3Button: 'Read more',
            service4Title: 'Coherence Assessment',
            service4Text: 'Ensure your essay flows smoothly.',
            service4Button: 'Read more',
            service5Title: 'Task Response Analysis',
            service5Text: 'Address task requirements effectively.',
            service5Button: 'Read more',
            contactTitle: 'Get in touch',
            formNameLabel: 'Name:',
            formEmailLabel: 'Email address:',
            formPhoneLabel: 'Phone number:',
            formMessageLabel: 'Message:',
            formSubmitButton: 'Submit',
            contactInfoTitle: 'Contact Information',
            contactInfoEmail: 'Email: ',
            contactInfoHours: 'Hours',
            hours: [
                'Monday: 9:00am - 10:00pm',
                'Tuesday: 9:00am - 10:00pm',
                'Wednesday: 9:00am - 10:00pm',
                'Thursday: 9:00am - 10:00pm',
                'Friday: 9:00am - 10:00pm',
                'Saturday: 9:00am - 6:00pm',
                'Sunday: 9:00am - 12:00pm'
            ]
        },
        zh: {
            heroText: '雅思作文批改服务，全⾯提高写作质量。',
            heroButton: '查看服务',
            aboutTitle: '专家作文批改',
            aboutText: '详细的作文评估和修改服务，重点关注四个关键领域：任务完成度、连贯性与一致性、词汇多样性和语法准确性。我们提供一个总体评分，帮助考生了解他们作文的总体水平。具体错误会用详细的改进建议进行标注，以提高写作质量。收到一个彻底修改后的作文，便于原文和修改后的版本对比，明确改进的地方。',
            contactButton: '联系我们',
            service1Title: '详细作文评估',
            service1Text: '获得深入的作文反馈。',
            service1Button: '了解更多',
            service2Title: '语法纠正',
            service2Text: '提高你的语法技能。',
            service2Button: '了解更多',
            service3Title: '词汇增强',
            service3Text: '扩展你的词汇量。',
            service3Button: '了解更多',
            service4Title: '连贯性评估',
            service4Text: '确保你的作文连贯流畅。',
            service4Button: '了解更多',
            service5Title: '任务回应分析',
            service5Text: '有效回应任务要求。',
            service5Button: '了解更多',
            contactTitle: '联系我们',
            formNameLabel: '姓名：',
            formEmailLabel: '电子邮件地址：',
            formPhoneLabel: '电话号码：',
            formMessageLabel: '留言：',
            formSubmitButton: '提交',
            contactInfoTitle: '联系信息',
            contactInfoEmail: '电子邮件：',
            contactInfoHours: '工作时间',
            hours: [
                '周一：上午9:00 - 晚上10:00',
                '周二：上午9:00 - 晚上10:00',
                '周三：上午9:00 - 晚上10:00',
                '周四：上午9:00 - 晚上10:00',
                '周五：上午9:00 - 晚上10:00',
                '周六：上午9:00 - 下午6:00',
                '周日：上午9:00 - 中午12:00'
            ]
        },
        fr: {
            heroText: 'Service de correction de dissertation IELTS, améliorez la qualité de l\'écriture.',
            heroButton: 'Voir les services',
            aboutTitle: 'Correction d\'essai par des experts',
            aboutText: 'Service d\'évaluation et de correction de dissertation détaillée se concentrant sur quatre domaines clés: l\'achèvement des tâches, la cohérence et la cohésion, la diversité du vocabulaire et la précision grammaticale. Nous fournissons un score global pour aider les candidats à comprendre le niveau global de leur dissertation. Les erreurs spécifiques sont soulignées avec des suggestions d\'amélioration détaillées pour améliorer la qualité de l\'écriture. Recevez une dissertation entièrement révisée pour comparaison entre la version originale et révisée, identifiant clairement les domaines à améliorer.',
            contactButton: 'Contactez-nous',
            service1Title: 'Évaluation détaillée de l\'essai',
            service1Text: 'Obtenez des commentaires approfondis sur votre essai.',
            service1Button: 'En savoir plus',
            service2Title: 'Correction grammaticale',
            service2Text: 'Améliorez vos compétences en grammaire.',
            service2Button: 'En savoir plus',
            service3Title: 'Amélioration du vocabulaire',
            service3Text: 'Élargissez votre répertoire de vocabulaire.',
            service3Button: 'En savoir plus',
            service4Title: 'Évaluation de la cohérence',
            service4Text: 'Assurez-vous que votre essai est fluide.',
            service4Button: 'En savoir plus',
            service5Title: 'Analyse de la réponse à la tâche',
            service5Text: 'Répondez efficacement aux exigences de la tâche.',
            service5Button: 'En savoir plus',
            contactTitle: 'Contactez-nous',
            formNameLabel: 'Nom:',
            formEmailLabel: 'Adresse e-mail:',
            formPhoneLabel: 'Numéro de téléphone:',
            formMessageLabel: 'Message:',
            formSubmitButton: 'Soumettre',
            contactInfoTitle: 'Informations de contact',
            contactInfoEmail: 'E-mail: ',
            contactInfoHours: 'Heures',
            hours: [
                'Lundi: 9h00 - 22h00',
                'Mardi: 9h00 - 22h00',
                'Mercredi: 9h00 - 22h00',
                'Jeudi: 9h00 - 22h00',
                'Vendredi: 9h00 - 22h00',
                'Samedi: 9h00 - 18h00',
                'Dimanche: 9h00 - 12h00'
            ]
        },
        de: {
            heroText: 'IELTS-Aufsatzkorrekturdienst, Verbesserung der Schreibqualität.',
            heroButton: 'Dienstleistungen anzeigen',
            aboutTitle: 'Experten-Aufsatzkorrektur',
            aboutText: 'Detaillierter Aufsatzbewertungs- und Korrekturservice, der sich auf vier Schlüsselbereiche konzentriert: Aufgabenerfüllung, Kohärenz und Kohäsion, Wortschatzvielfalt und grammatikalische Genauigkeit. Wir bieten eine Gesamtnote, um den Kandidaten zu helfen, das Gesamtniveau ihres Aufsatzes zu verstehen. Spezifische Fehler werden mit detaillierten Verbesserungsvorschlägen hervorgehoben, um die Schreibqualität zu verbessern. Erhalten Sie einen gründlich überarbeiteten Aufsatz zum Vergleich zwischen der Original- und der überarbeiteten Version, wobei die zu verbessernden Bereiche klar identifiziert werden.',
            contactButton: 'Kontaktieren Sie uns',
            service1Title: 'Detaillierte Aufsatzbewertung',
            service1Text: 'Erhalten Sie detailliertes Feedback zu Ihrem Aufsatz.',
            service1Button: 'Mehr erfahren',
            service2Title: 'Grammatik-Korrektur',
            service2Text: 'Verbessern Sie Ihre Grammatikkenntnisse.',
            service2Button: 'Mehr erfahren',
            service3Title: 'Wortschatzverbesserung',
            service3Text: 'Erweitern Sie Ihr Wortschatzrepertoire.',
            service3Button: 'Mehr erfahren',
            service4Title: 'Kohärenzbewertung',
            service4Text: 'Stellen Sie sicher, dass Ihr Aufsatz flüssig ist.',
            service4Button: 'Mehr erfahren',
            service5Title: 'Aufgabenantwort-Analyse',
            service5Text: 'Erfüllen Sie die Aufgabenanforderungen effektiv.',
            service5Button: 'Mehr erfahren',
            contactTitle: 'Kontaktieren Sie uns',
            formNameLabel: 'Name:',
            formEmailLabel: 'E-Mail-Adresse:',
            formPhoneLabel: 'Telefonnummer:',
            formMessageLabel: 'Nachricht:',
            formSubmitButton: 'Einreichen',
            contactInfoTitle: 'Kontaktinformation',
            contactInfoEmail: 'E-Mail: ',
            contactInfoHours: 'Öffnungszeiten',
            hours: [
                'Montag: 9:00 - 22:00 Uhr',
                'Dienstag: 9:00 - 22:00 Uhr',
                'Mittwoch: 9:00 - 22:00 Uhr',
                'Donnerstag: 9:00 - 22:00 Uhr',
                'Freitag: 9:00 - 22:00 Uhr',
                'Samstag: 9:00 - 18:00 Uhr',
                'Sonntag: 9:00 - 12:00 Uhr'
            ]
        },
        jp: {
            heroText: 'IELTS作文の添削サービス、ライティング品質の向上。',
            heroButton: 'サービスを見る',
            aboutTitle: 'エキスパートによる作文の添削',
            aboutText: 'タスク完了度、一貫性と連結性、語彙の多様性、文法の正確性という4つの重要な分野に焦点を当てた詳細なエッセイ評価および修正サービスを提供します。受験者がエッセイの全体的なレベルを理解できるように総合評価を提供します。具体的なエラーは、ライティングの質を向上させるための詳細な改善提案とともに強調表示されます。オリジナルと修正されたバージョンの比較のために徹底的に修正されたエッセイを受け取り、改善が必要な領域を明確に特定します。',
            contactButton: 'お問い合わせ',
            service1Title: '詳細な作文評価',
            service1Text: 'エッセイに関する詳細なフィードバックを受け取る。',
            service1Button: 'もっと詳しく',
            service2Title: '文法修正',
            service2Text: '文法スキルを向上させる。',
            service2Button: 'もっと詳しく',
            service3Title: '語彙の強化',
            service3Text: '語彙のレパートリーを拡大する。',
            service3Button: 'もっと詳しく',
            service4Title: '一貫性の評価',
            service4Text: 'エッセイがスムーズに流れるようにする。',
            service4Button: 'もっと詳しく',
            service5Title: 'タスク応答分析',
            service5Text: 'タスクの要求を効果的に満たす。',
            service5Button: 'もっと詳しく',
            contactTitle: 'お問い合わせ',
            formNameLabel: '名前：',
            formEmailLabel: 'メールアドレス：',
            formPhoneLabel: '電話番号：',
            formMessageLabel: 'メッセージ：',
            formSubmitButton: '送信',
            contactInfoTitle: '連絡先情報',
            contactInfoEmail: 'メールアドレス：',
            contactInfoHours: '営業時間',
            hours: [
                '月曜日：9:00〜22:00',
                '火曜日：9:00〜22:00',
                '水曜日：9:00〜22:00',
                '木曜日：9:00〜22:00',
                '金曜日：9:00〜22:00',
                '土曜日：9:00〜18:00',
                '日曜日：9:00〜12:00'
            ]
        }
    };

    document.getElementById('hero-text').textContent = texts[lang].heroText;
    document.getElementById('hero-button').textContent = texts[lang].heroButton;
    document.getElementById('about-title').textContent = texts[lang].aboutTitle;
    document.getElementById('about-text').textContent = texts[lang].aboutText;
    document.getElementById('contact-button').textContent = texts[lang].contactButton;
    document.getElementById('service1-title').textContent = texts[lang].service1Title;
    document.getElementById('service1-text').textContent = texts[lang].service1Text;
    document.getElementById('service1-button').textContent = texts[lang].service1Button;
    document.getElementById('service2-title').textContent = texts[lang].service2Title;
    document.getElementById('service2-text').textContent = texts[lang].service2Text;
    document.getElementById('service2-button').textContent = texts[lang].service2Button;
    document.getElementById('service3-title').textContent = texts[lang].service3Title;
    document.getElementById('service3-text').textContent = texts[lang].service3Text;
    document.getElementById('service3-button').textContent = texts[lang].service3Button;
    document.getElementById('service4-title').textContent = texts[lang].service4Title;
    document.getElementById('service4-text').textContent = texts[lang].service4Text;
    document.getElementById('service4-button').textContent = texts[lang].service4Button;
    document.getElementById('service5-title').textContent = texts[lang].service5Title;
    document.getElementById('service5-text').textContent = texts[lang].service5Text;
    document.getElementById('service5-button').textContent = texts[lang].service5Button;
    document.getElementById('contact-title').textContent = texts[lang].contactTitle;
    document.getElementById('form-name-label').textContent = texts[lang].formNameLabel;
    document.getElementById('form-email-label').textContent = texts[lang].formEmailLabel;
    document.getElementById('form-phone-label').textContent = texts[lang].formPhoneLabel;
    document.getElementById('form-message-label').textContent = texts[lang].formMessageLabel;
    document.getElementById('form-submit-button').textContent = texts[lang].formSubmitButton;
    document.getElementById('contact-info-title').textContent = texts[lang].contactInfoTitle;
    document.getElementById('contact-info-email').textContent = texts[lang].contactInfoEmail;
    document.getElementById('contact-info-hours').textContent = texts[lang].contactInfoHours;
    const hoursList = document.getElementById('contact-info-hours').nextElementSibling;
    while (hoursList.firstChild) {
        hoursList.removeChild(hoursList.firstChild);
    }
    texts[lang].hours.forEach(hour => {
        const p = document.createElement('p');
        p.textContent = hour;
        hoursList.appendChild(p);
    });
}

// Initial setup
document.addEventListener('DOMContentLoaded', () => {
    addTranslationButton();
});
