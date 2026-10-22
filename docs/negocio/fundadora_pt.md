# Papel de fundadora: Embrapa e USP (issue #17)

*Isto não é parecer jurídico.* É um mapa do que a lei e as políticas públicas dizem, das perguntas a fazer e das estruturas possíveis. As respostas que valem são as escritas pelos dois escritórios de inovação. Antes de assinar o contrato social, leve-as a um advogado.

## Situação

- Você aguarda a posse como pesquisadora da Embrapa (concurso 2024). É doutoranda da USP e está como pesquisadora visitante na Universidade de Illinois.
- O código deste repositório foi escrito agora, com dados públicos (IBGE, NASA, MODIS, Sentinel-2, MapBiomas, ZARC). Os dados dos seus experimentos de doutorado (eCO2 × seca × temperatura) e a meta-análise ainda **não** entraram no índice (issue #8).
- Isso importa porque a pergunta sobre quem é dono do quê depende de **quando** e **com quais recursos** cada parte foi feita.
- **O código está sob licença MIT** (arquivo `LICENSE`): qualquer pessoa, inclusive concorrentes, pode copiá-lo e usá-lo comercialmente. Isso ajuda na credibilidade (backtest aberto) e deixa claro que o índice é anterior à posse, mas o código em si não é um ativo protegido. O que dá para proteger: a marca, o registro semanal ao vivo, os dados de clientes e de campo, a calibração com os seus experimentos e os modelos por talhão. Decida, antes de fazer essas partes, se elas ficam em um repositório **privado**.

## O que já se sabe

**Lei de Inovação (Lei 10.973/2004, alterada pela Lei 13.243/2016), art. 15:** a administração pode conceder ao pesquisador público que **não esteja em estágio probatório** uma licença sem remuneração para constituir empresa de inovação. A licença dura até 3 anos consecutivos, renováveis por igual período.

**Política de Inovação da Embrapa** ([documento](https://portal-p2.sede.embrapa.br/documents/10180/36044282/Pol%C3%ADtica+de+Inova%C3%A7%C3%A3o+da+Embrapa/59d4b2d6-d948-5228-52f7-65f6ecf0c38c)):

- **item 8.5.2(e):** a Embrapa pode conceder licença sem remuneração ao pesquisador **fora do período de experiência** para constituir empresa;
- **item 8.5.2(c):** pode ceder seus direitos de propriedade intelectual aos criadores e a terceiros;
- **item 8.5.2(d):** pode autorizar o empregado a participar dos ganhos econômicos de tecnologias que criou.

O documento não trata de empregado como sócio de startup nem de conflito de interesses; essas são as perguntas abertas.

**Consequência prática:** logo depois da posse você estará em período de experiência, e nessa fase a licença não pode ser concedida. A empresa, portanto, precisa de um administrador que não seja você desde o começo.

**FAPESP PIPE** (ver issue #20): o pesquisador responsável precisa ser **sócio** da empresa, **morar no estado de São Paulo** durante o projeto e dedicar pelo menos 24 h por semana. Mestrandos e doutorandos não podem ser pesquisadores principais. Se o seu posto na Embrapa não for em SP, ou se a Embrapa não autorizar as 24 h, o pesquisador responsável do PIPE terá de ser outra pessoa: o cofundador de dados ou outro sócio com perfil técnico.

## Perguntas para a Embrapa (Núcleo de Inovação ou setor de Transferência de Tecnologia)

1. Um empregado pesquisador pode ser **sócio quotista** de uma startup, sem ser administrador, durante o período de experiência e depois dele?
2. Pode ser **administrador**? Em que condições?
3. A licença sem remuneração do item 8.5.2(e) vale para quem tomou posse há pouco tempo? Quanto dura o período de experiência?
4. Se eu continuar trabalhando na empresa fora do horário (noites e fins de semana), o que preciso declarar? Há regra de conflito de interesses, por exemplo se a empresa vender para clientes que também são parceiros da Embrapa?
5. Quem é dono de um índice desenvolvido **antes da posse**, com dados públicos e código já publicado (licença do repositório)? E das melhorias feitas depois da posse?
6. Se a Embrapa quiser participar (dados do ZARC, ensaios de cultivares, rede de estações), qual é o caminho: acordo de parceria, licenciamento, participação no capital?
7. A Embrapa tem programa de apoio a spin-offs ou incubação (por exemplo, a Rede Embrapa de Incubação) aberto a empregados?

## Perguntas para a Agência USP de Inovação (AUSPIN)

1. O índice e o código deste repositório foram feitos durante o doutorado, mas sem dados do doutorado, sem equipamento da USP e sem financiamento de projeto USP. A USP tem algum direito sobre eles?
2. Se eu usar no produto os dados dos meus experimentos de doutorado (issue #8), o que muda? Precisa de licença da USP? Quem mais tem direito (orientador, agência de fomento, coautores)?
3. Minha bolsa de doutorado (informe qual, se houver) permite ser sócia de empresa? Precisa de autorização?
4. Como funciona o licenciamento de tecnologia USP para startup (royalties, exclusividade, prazos)?
5. Uma startup de doutoranda da USP pode entrar nas incubadoras USP (Cietec/Incubadora USP/Ipen, ESALQTec, Habits) antes de existir o CNPJ?

## E-mails prontos

**Para a Embrapa:**

> **Assunto:** Consulta sobre participação de pesquisadora em startup (Política de Inovação, item 8.5.2)
>
> Prezados, sou Janaina Fortirer, aprovada no concurso Embrapa 2024 para o cargo de pesquisadora e aguardando posse. Antes da posse, desenvolvi com dados públicos um índice de estresse hídrico e térmico da soja (código aberto em github.com/Fortirer/soy-stress-index) e pretendo criar uma startup para oferecê-lo a cooperativas, bancos e seguradoras.
>
> Gostaria de orientação por escrito sobre: (1) se posso ser sócia quotista e/ou administradora durante e após o período de experiência; (2) as condições da licença sem remuneração prevista no item 8.5.2(e) da Política de Inovação e no art. 15 da Lei 10.973/2004; (3) a titularidade do índice criado antes da posse e de melhorias posteriores; (4) regras de conflito de interesses; (5) caminhos para eventual parceria com a Embrapa.
>
> Posso enviar mais detalhes ou conversar por videochamada. Obrigada.

**Para a AUSPIN:**

> **Assunto:** Propriedade intelectual de índice desenvolvido durante doutorado e criação de startup
>
> Prezados, sou Janaina Fortirer, doutoranda da USP (programa [ ], orientação de [ ]). Desenvolvi um índice de estresse da soja a partir de dados públicos de satélite e clima, com código aberto (github.com/Fortirer/soy-stress-index), sem uso de dados, equipamentos ou recursos de projetos da USP. Pretendo criar uma startup para oferecê-lo ao mercado e, no futuro, calibrar o índice com dados dos meus experimentos de doutorado.
>
> Gostaria de orientação sobre: (1) eventuais direitos da USP sobre o índice e o código; (2) o que muda se dados do doutorado forem usados; (3) se a bolsa permite participação societária; (4) como funciona o licenciamento USP para startups; (5) acesso às incubadoras USP antes do CNPJ.
>
> Obrigada.

## Estruturas possíveis (a decidir com as respostas)

| Opção | Como fica | Prós | Contras |
| --- | --- | --- | --- |
| **A. Sócia minoritária, sem administração** | Cofundador de negócios é o administrador; você é sócia técnica e conselheira | Funciona desde o início, mesmo no período de experiência (se a Embrapa autorizar ser sócia) | Precisa de cofundador já (#18); menos controle formal |
| **B. Licença sem remuneração** | Depois do período de experiência, você sai da Embrapa por até 3 + 3 anos e lidera a empresa | Dedicação total; você pode ser pesquisadora responsável do PIPE (se a empresa for em SP) | Sem salário; só depois do período de experiência |
| **C. Embrapa como parceira** | Acordo de parceria ou licença com a Embrapa; a empresa é de outros sócios e você colabora pelo lado da Embrapa | Sem conflito; acesso a dados e marca da Embrapa | Você não é dona; mais lento |
| **D. Abrir antes da posse** | Constituir a empresa agora, com o cofundador como administrador, e declarar tudo na posse | Deixa claro que o índice é anterior à posse | Depende da resposta 5 da Embrapa; exige cofundador agora |

## Próximo passo

1. Envie os dois e-mails esta semana.
2. Responda as perguntas da AUSPIN sobre programa, orientador e bolsa nos campos [ ].
3. Registre as respostas nesta issue.
4. Escolha a estrutura junto com o cofundador (#18) antes do PIPE (#20) e da incubadora (#21).
