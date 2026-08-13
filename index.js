// visionDS — DeepSeek Harness 技能 bundle 入口。
// 安装（dsh plugin add github:deveuper/visionDS）后，本插件在应用时把
// skill/SKILL.md 注册为运行时技能 vision-ds，资源基目录指向包内 skill/ 目录。
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const skillDir = join(dirname(fileURLToPath(import.meta.url)), 'skill')

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

export function apply(ctx) {
  const { meta, body } = parseFrontmatter(readFileSync(join(skillDir, 'SKILL.md'), 'utf8'))
  ctx.skills.register({
    name: meta.name,
    description: meta.description ?? '',
    whenToUse: meta.whenToUse,
    content: body,
    resourceBase: { kind: 'directory', path: skillDir },
  })
}
