# Contributing to MedExtract

Thank you for your interest in contributing to MedExtract! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Issues

1. **Check existing issues** to avoid duplicates
2. **Use issue templates** when available
3. **Provide detailed information**:
   - System configuration
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages and logs

### Suggesting Features

1. **Open a discussion** first for major features
2. **Describe the use case** clearly
3. **Consider implementation complexity**
4. **Align with project goals**

### Submitting Code

#### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/your-username/medextract.git
cd medextract

# Create a new branch
git checkout -b feature/your-feature-name

# Install development dependencies
docker-compose -f docker-compose.dev.yml build
```

#### Development Workflow

1. **Make changes** in your feature branch
2. **Test thoroughly**:
   ```bash
   # Run backend tests
   docker-compose run backend pytest
   
   # Run frontend tests
   docker-compose run frontend npm test
   ```

3. **Follow code style**:
   - Python: PEP 8
   - TypeScript/JavaScript: ESLint configuration
   - Use meaningful variable names
   - Add comments for complex logic

4. **Commit changes**:
   ```bash
   git add .
   git commit -m "feat: add new extraction strategy"
   ```

   Commit message format:
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation changes
   - `style:` formatting changes
   - `refactor:` code restructuring
   - `test:` test additions/changes
   - `chore:` maintenance tasks

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

#### Pull Request Guidelines

1. **Title**: Clear and descriptive
2. **Description**: 
   - What changes were made
   - Why they were necessary
   - How they were tested
3. **Link related issues**
4. **Ensure CI passes**
5. **Request reviews**

### Code Review Process

1. **Automated checks** must pass
2. **At least one approval** required
3. **Address feedback** constructively
4. **Keep PR scope focused**

## Development Guidelines

### Backend (Python/FastAPI)

```python
# Good practice example
async def extract_datapoint(
    text: str,
    config: DatapointConfig,
    llm_client: LLMClient
) -> ExtractedData:
    """
    Extract a single datapoint from text.
    
    Args:
        text: Input medical report text
        config: Datapoint configuration
        llm_client: LLM client instance
        
    Returns:
        ExtractedData object with results
    """
    # Implementation here
    pass
```

### Frontend (TypeScript/Next.js)

```typescript
// Good practice example
interface ExtractionJobProps {
  jobId: string;
  onComplete?: (result: ExtractionResult) => void;
}

export const ExtractionJob: React.FC<ExtractionJobProps> = ({
  jobId,
  onComplete
}) => {
  // Component implementation
};
```

### Docker and DevOps

- Keep Dockerfiles minimal
- Use multi-stage builds
- Pin dependency versions
- Document environment variables

## Testing

### Unit Tests
- Test individual functions/components
- Mock external dependencies
- Aim for >80% coverage

### Integration Tests
- Test API endpoints
- Test component interactions
- Test Docker configurations

### End-to-End Tests
- Test complete workflows
- Test error scenarios
- Test performance limits

## Documentation

### Code Documentation
- Docstrings for all public functions
- JSDoc comments for TypeScript
- Inline comments for complex logic

### User Documentation
- Update user guide for new features
- Include screenshots when relevant
- Keep installation guide current

### API Documentation
- Update OpenAPI schemas
- Document new endpoints
- Provide example requests/responses

## Release Process

1. **Version numbering**: Semantic versioning (MAJOR.MINOR.PATCH)
2. **Changelog**: Update CHANGELOG.md
3. **Testing**: Full test suite passes
4. **Documentation**: All docs updated
5. **Release notes**: Clear description of changes

## Getting Help

- **Discord**: [Join our community](https://discord.gg/medextract)
- **GitHub Discussions**: For questions and ideas
- **Email**: dev@medextract.org

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to MedExtract!