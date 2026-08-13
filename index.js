// visionDS — DeepSeek Harness 技能 bundle 入口。
// 安装（dsh plugin add github:deveuper/visionDS）后，本插件在应用时把
// skills/ 下的四个技能注册为运行时技能：vision-ds（默认入口，API 超时
// 自动回退本地）、vision-ds-local（离线 OCR）、vision-ds-api（API 识别）、
// vision-setting（配置中枢）。资源基目录指向各自的技能目录；其余三个
// 技能通过同级 `../vision-ds` 引用共享脚本。
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const skillsRoot = join(dirname(fileURLToPath(import.meta.url)), 'skills')

export const name = 'vision-ds'
export const inject = ['skills']

function parseFrontmatter(raw) {
  const match = /^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/.exec(raw)
  if (!match) throw new Error('vision-ds: SKILL.md 缺少 YAML frontmatter')
  const meta = {}
  for (const line of match[1].split(/\r?\n/)) {
    const hit = /^([A-Za-z-]+):\s*(.*)$/.exec(line)
    if (hit) meta[hit[1]] = hit[2].trim()
  }
  return { meta, body: match[2] }
}

/** 读取一个技能的 frontmatter 与正文，并给出其资源基目录。 */
function loadSkill(skillName) {
  const skillDir = join(skillsRoot, skillName)
  const { meta, body } = parseFrontmatter(readFileSync(join(skillDir, 'SKILL.md'), 'utf8'))
  return {
    name: meta.name,
    description: meta.description ?? '',
    whenToUse: meta.whenToUse,
    content: body,
    resourceBase: { kind: 'directory', path: skillDir },
  }
}

export function apply(ctx) {
  for (const skillName of ['vision-ds', 'vision-ds-local', 'vision-ds-api', 'vision-setting']) {
    ctx.skills.register(loadSkill(skillName))
  }
}
